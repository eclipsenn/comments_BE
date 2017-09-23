SET ROLE 'exness';

INSERT INTO users VALUES('user1', 'dmitry', 'mishin');
INSERT INTO users VALUES('user2', 'yana', 'kovaleva');

INSERT INTO entities(type, creator, user_last_modified, text) VALUES('post', 'user1', 'user1', 'some post');
INSERT INTO entities(type, creator, user_last_modified, text) VALUES('post', 'user2', 'user2', 'another post');

INSERT INTO entities(type, creator, user_last_modified, text, ancestor_id) VALUES('comment', 'user1', 'user1', 'new comment by dima', 1);
INSERT INTO entities(type, creator, user_last_modified, text, ancestor_id) VALUES('comment', 'user2', 'user2', 'new comment by yana', 2);

INSERT INTO entities(type, creator, user_last_modified, text, ancestor_id) VALUES('comment', 'user1', 'user1', 'dima commented some comment', 5);
INSERT INTO entities(type, creator, user_last_modified, text, ancestor_id) VALUES('comment', 'user2', 'user2', 'yana commented some comment', 6);