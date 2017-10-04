--Commented out as docker provides a convenient shortcut of this
--specified in docker-compose.yml

--CREATE SCHEMA IF NOT EXISTS public
--  AUTHORIZATION postgres;
--GRANT ALL ON SCHEMA public TO postgres;
--GRANT ALL ON SCHEMA public TO public;

--SET ROLE 'postgres';

--DROP DATABASE IF EXISTS comments_db;
--DROP ROLE IF EXISTS dmishin;
--CREATE USER dmishin WITH PASSWORD 'dmishin';
--CREATE DATABASE comments_db ENCODING 'UTF8';
--GRANT ALL PRIVILEGES ON DATABASE comments_db TO dmishin;

--SET ROLE 'dmishin';

DROP TYPE IF EXISTS entity_type CASCADE;
CREATE TYPE entity_type AS ENUM('post', 'comment', 'page');
DROP TYPE IF EXISTS action_type CASCADE;
CREATE TYPE action_type AS ENUM('create', 'update', 'delete', 'restore');

DROP TABLE IF EXISTS users CASCADE;
CREATE TABLE "users" (
    "username" varchar(100) PRIMARY KEY,
    "first_name" varchar(100) NOT NULL,
    "second_name" varchar(100) NOT NULL
);

DROP TABLE IF EXISTS entities CASCADE;
CREATE TABLE "entities" (
    "type" entity_type NOT NULL,
    "id" INTEGER NOT NULL,
    PRIMARY KEY (type, id)
);


DROP TABLE IF EXISTS entities_metadata CASCADE;
CREATE TABLE "entities_metadata" (
    "id" serial PRIMARY KEY,
    "creator" varchar(100) NOT NULL REFERENCES "users"("username"),
    "date_created" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "date_last_modified" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "user_last_modified" varchar(100) NOT NULL REFERENCES "users"("username"),
    "text" varchar NOT NULL,
    "type" entity_type NOT NULL,
    "parent_type" entity_type,
    "parent_id" INTEGER,
    FOREIGN KEY ("type", "id") REFERENCES entities("type", "id"),
    FOREIGN KEY ("parent_type", "parent_id") REFERENCES entities("type", "id")
);


DROP TABLE IF EXISTS entities_closure_table CASCADE;
CREATE TABLE "entities_closure_table" (
    "id" serial PRIMARY KEY,
    "ancestor_type" entity_type NOT NULL,
    "ancestor_id" INTEGER,
    "descendant_type" entity_type NOT NULL,
    "descendant_id" INTEGER,
    FOREIGN KEY (ancestor_type, ancestor_id) REFERENCES entities(type, id),
    FOREIGN KEY (descendant_type, descendant_id) REFERENCES entities(type, id)
);


DROP TABLE IF EXISTS "comments" CASCADE;
CREATE TABLE "comments" (
    "id" serial PRIMARY KEY,
    "type" entity_type CHECK("type"='comment'),
    "parent_type" entity_type,
    "parent_id" INTEGER,
    FOREIGN KEY ("type", "id") REFERENCES entities("type", "id"),
    FOREIGN KEY ("parent_type", "parent_id") REFERENCES entities("type", "id")
) INHERITS (entities_metadata);


DROP TABLE IF EXISTS "posts" CASCADE;
CREATE TABLE "posts" (
    "id" serial PRIMARY KEY,
    "type" entity_type CHECK("type"='post'),
    "parent_type" entity_type CHECK("parent_type"=NULL),
    "parent_id" INTEGER CHECK("parent_id"=NULL),
    FOREIGN KEY ("type", "id") REFERENCES entities("type", "id")
) INHERITS (entities_metadata);


DROP TABLE IF EXISTS history CASCADE;
CREATE TABLE "history" (
    "id" SERIAL PRIMARY KEY,
    "entity_type" entity_type NOT NULL DEFAULT 'comment',
    "entity_id" INTEGER NOT NULL,
    "user"   VARCHAR(100),
    "action" action_type NOT NULL,
    "date" TIMESTAMP WITH TIME ZONE,
    "text" varchar,
    "parent_type" entity_type,
    "parent_id" INTEGER
);


-- add post/comment to entities.

CREATE OR REPLACE function create_entity() RETURNS TRIGGER
  AS $$
    BEGIN
      INSERT INTO entities ("type", "id")
      VALUES (NEW.type, NEW.id);

      IF NEW.type = 'post' THEN
        INSERT INTO entities_closure_table ("ancestor_type", "ancestor_id", "descendant_type", "descendant_id")
        VALUES(NEW.type, NEW.id, NEW.type, NEW.id);
      ELSIF NEW.type = 'comment' THEN
        INSERT INTO entities_closure_table ("ancestor_type", "ancestor_id", "descendant_type", "descendant_id")
        SELECT ancestor_type, ancestor_id, NEW.type, NEW.id
        FROM entities_closure_table as ect
        WHERE ect.descendant_type = NEW.parent_type and ect.descendant_id = NEW.parent_id
        UNION ALL
        SELECT NEW.type, NEW.id, NEW.type, NEW.id;
      END IF;
      RETURN NEW;
    END
  $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_create_post_to_entity ON posts;
CREATE TRIGGER tr_create_post_to_entity BEFORE INSERT ON posts
  FOR EACH ROW EXECUTE PROCEDURE create_entity();

DROP TRIGGER IF EXISTS tr_create_comment_to_entity ON comments;
CREATE TRIGGER tr_create_comment_to_entity BEFORE INSERT ON comments
  FOR EACH ROW EXECUTE PROCEDURE create_entity();


-- delete post/comment from entities. Only possible to remove when there's no children

CREATE OR REPLACE function delete_entity() RETURNS TRIGGER
  AS $$
    BEGIN
      DELETE FROM entities_closure_table
      WHERE descendant_type = OLD.type and descendant_id = OLD.id;

      DELETE FROM entities
      WHERE type = OLD.type and id=OLD.id;

      RETURN NEW;
    END
  $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_delete_post_to_entity ON posts;
CREATE TRIGGER tr_delete_post_to_entity AFTER DELETE ON posts
  FOR EACH ROW EXECUTE PROCEDURE delete_entity();

DROP TRIGGER IF EXISTS tr_delete_comment_to_entity ON comments;
CREATE TRIGGER tr_delete_post_to_entity AFTER DELETE ON comments
  FOR EACH ROW EXECUTE PROCEDURE delete_entity();


-- create_comment_to_history  - triggers create_comment_to_history

CREATE OR REPLACE function update_history() RETURNS TRIGGER
  AS $$
    DECLARE
      _id integer;
      _user_last_modified varchar(100);
      _action action_type;
      _text varchar;

    BEGIN
      IF TG_OP = 'INSERT' THEN _id=NEW.id; _user_last_modified=NEW.user_last_modified; _action = 'create'; _text=NEW.text;
      ELSIF TG_OP = 'UPDATE' THEN _id=NEW.id; _user_last_modified=NEW.user_last_modified; _action = 'update'; _text=NEW.text;
      ELSIF TG_OP = 'DELETE' THEN _id=OLD.id; _user_last_modified=OLD.user_last_modified; _action = 'delete'; _text=OLD.text;
      END IF;
      INSERT INTO history ("entity_id", "user", "action", "date", "text")
      VALUES(_id, _user_last_modified, _action, CURRENT_TIMESTAMP, _text);
      RETURN NEW;
    END
  $$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS tr_update_history ON comments;
CREATE TRIGGER tr_update_history AFTER INSERT OR UPDATE OR DELETE ON comments
  FOR EACH ROW EXECUTE PROCEDURE update_history();


DROP TABLE IF EXISTS search_history;
CREATE TABLE search_history (
  "id" SERIAL PRIMARY KEY,
  "user" varchar(100) NOT NULL,
  "start_date" TIMESTAMP WITH TIME ZONE,
  "end_date" TIMESTAMP WITH TIME ZONE,
  "search_date" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "root_entity_type" entity_type,
  "root_entity_id" INTEGER
);
