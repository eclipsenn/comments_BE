SET ROLE 'dmishin';

INSERT INTO users VALUES('user1', 'dmitry', 'mishin');
INSERT INTO users VALUES('user2', 'yana', 'kovaleva');
INSERT INTO users VALUES('user3', 'test', 'test_surname');

INSERT INTO posts(type, creator, user_last_modified, text) VALUES('post', 'user1', 'user1', 'some post');
INSERT INTO posts(type, creator, user_last_modified, text) VALUES('post', 'user2', 'user2', 'another post');

INSERT INTO comments(type, creator, user_last_modified, text, parent_type, parent_id) VALUES('comment', 'user1', 'user1', 'new comment by dima', 'post',  1);
INSERT INTO comments(type, creator, user_last_modified, text, parent_type, parent_id) VALUES('comment', 'user2', 'user2', 'new comment by yana', 'post',  2);

INSERT INTO comments(type, creator, user_last_modified, text, parent_type, parent_id) VALUES('comment', 'user1', 'user1', 'dima commented some comment', 'comment',  1);
INSERT INTO comments(type, creator, user_last_modified, text, parent_type, parent_id) VALUES('comment', 'user2', 'user2', 'yana commented some comment', 'comment',  2);
