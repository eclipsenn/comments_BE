SET ROLE 'exness';

BEGIN;

CREATE TYPE ancestor_type AS ENUM('post', 'comment');

CREATE TYPE action_type AS ENUM('create', 'update', 'delete', 'restore');

DROP TABLE IF EXISTS users;
CREATE TABLE "users" (
    "username" varchar(100) PRIMARY KEY,
    "first_name" varchar(100) NOT NULL,
    "second_name" varchar(100) NOT NULL
);

DROP TABLE IF EXISTS entities;
CREATE TABLE "entities" (
    "id" serial PRIMARY KEY,
    "type" ancestor_type NOT NULL,
    "creator" varchar(100) NOT NULL REFERENCES "users"("username"),
    "date_created" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "date_last_modified" TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    "user_last_modified" varchar(100) NOT NULL REFERENCES "users"("username"),
    "text" varchar,
    "ancestor_id" INTEGER REFERENCES "entities" ("id")
);

DROP TABLE IF EXISTS history;
CREATE TABLE "history" (
    "id" SERIAL PRIMARY KEY,
    "entity_id" INTEGER,
    "user"   VARCHAR(100),
    "action" action_type NOT NULL,
    "date" TIMESTAMP WITH TIME ZONE,
    "text" varchar
);

CREATE VIEW comments AS
  SELECT * from entities
    WHERE type='comment';


CREATE OR REPLACE function create_comment() RETURNS TRIGGER
  AS $$
    BEGIN
      INSERT INTO history ("entity_id", "user", "action", "date", "text")
      VALUES(NEW.id, NEW.user_last_modified, 'create', CURRENT_TIMESTAMP, NEW.text);
      RETURN NEW;
    END
  $$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS tr_create_comment ON entities;
CREATE TRIGGER tr_create_comment AFTER INSERT ON entities
  FOR EACH ROW EXECUTE PROCEDURE create_comment();


CREATE OR REPLACE function update_comment() RETURNS TRIGGER
  AS $$
    BEGIN
      IF NEW.text IS NULL THEN
        INSERT INTO history ("entity_id", "user", "action", "date", "text")
        VALUES(NEW.id, NEW.user_last_modified, 'delete', CURRENT_TIMESTAMP, OLD.text);
      ELSIF OLD.TEXT IS NULL THEN
        INSERT INTO history ("entity_id", "user", "action", "date", "text")
        VALUES(NEW.id, NEW.user_last_modified, 'restore', CURRENT_TIMESTAMP, NEW.text);
      ELSE
        INSERT INTO history ("entity_id", "user", "action", "date", "text")
        VALUES(NEW.id, NEW.user_last_modified, 'update', CURRENT_TIMESTAMP, NEW.text);
      END IF ;
      RETURN NEW;
    END
  $$ LANGUAGE plpgsql;


DROP TRIGGER IF EXISTS tr_update_comment ON entities;
CREATE TRIGGER tr_update_comment AFTER UPDATE ON entities
  FOR EACH ROW EXECUTE PROCEDURE update_comment();

DROP TABLE IF EXISTS search_history;
CREATE TABLE search_history (
  "id" SERIAL PRIMARY KEY,
  "user" varchar(100) NOT NULL,
  "start_date" TIMESTAMP WITH TIME ZONE,
  "end_date" TIMESTAMP WITH TIME ZONE,
  "search_date" TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP,
  "root_comment_id" INTEGER
);


COMMIT;
