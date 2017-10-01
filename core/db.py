"""
Module to interact with postgres DB.

ORM can be supported by sqlalchemy. Performance is questionable though.
aiopg SELECT operation returns `list` of results
https://github.com/aio-libs/aiopg/blob/master/aiopg/sa/result.py#L366
which might cost much memory, use it carefully.
"""
# TODO: db injection handling

from datetime import datetime

import aiopg.sa

# ORM is not implemented but quite possible to be
# Example below is based on SQLAlchemy ORM

# import sqlalchemy as sa
#from datetime import datetime
# from sqlalchemy.ext.declarative import declarative_base

# meta = sa.MetaData()
# entity_types = sa.Enum('comment', 'post')

# Base = declarative_base()

# class Users(Base):
#     __tablename__ = 'users'
#
#     username = sa.Column(sa.String(100), primary_key=True)
#     first_name = sa.Column(sa.String(100), nullable=False)
#     second_name = sa.Column(sa.String(100), nullable=False)
#
#
# class Entities(Base):
#     __tablename__ = 'entities'
#
#     id = sa.Column(sa.Integer, primary_key=True)
#     type = sa.Column(entity_types, nullable=False)
#     creator = sa.Column(sa.String(100), sa.ForeignKey('users.username'), nullable=False)
#     date_created = sa.Column(sa.DateTime(timezone=True), default=datetime.now())
#     date_last_modified = sa.Column(sa.DateTime(timezone=True), default=datetime.now())
#     text = sa.Column(sa.String(), nullable=False)
#
#     __mapper_args__ = {
#         'polymorphic_on': type
#     }
#
#
# class Posts(Entities):
#     __tablename__ = 'posts'
#
#     id = sa.Column(sa.Integer, sa.ForeignKey('entities.id'), primary_key=True)
#     parent_id = sa.Column(sa.Integer(), sa.CheckConstraint('parent_id is NULL'))
#     #type = sa.Column(entity_types, sa.CheckConstraint('type = post'))
#     __mapper_args__ = {
#         'polymorphic_identity': 'post',
#     }
#
#
# class Comments(Entities):
#     __tablename__ = 'comments'
#
#     id = sa.Column(sa.Integer, sa.ForeignKey('entities.id'), primary_key=True)
#     parent_id = sa.Column(sa.Integer())
#     #type = sa.Column(entity_types, sa.CheckConstraint('type = comment'))
#     __mapper_args__ = {
#         'polymorphic_identity': 'comment',
#     }


# users = sa.Table(
#     'users', meta,
#     sa.Column('username', sa.String(100), primary_key=True),
#     sa.Column('first_name', sa.String(100), nullable=False),
#     sa.Column('second_name', sa.String(100), nullable=False),
# )
#
# entities = sa.Table(
#     'entities', meta,
#     sa.Column('id', sa.Integer(), primary_key=True),
#     sa.Column('type', sa.String(), nullable=False),
#     sa.Column('creator', sa.ForeignKey(users.c.username, ondelete='CASCADE'), nullable=False),
#     sa.Column('date_created', sa.DateTime(timezone=True), default=datetime.now()),
#     sa.Column('date_last_modified', sa.DateTime(timezone=True), default=datetime.now()),
#     sa.Column('text', sa.String(), nullable=False),
#     sa.Column('parent_id', sa.Integer()),
# )
#
# comments = sa.Table(
#     'comments', meta,
#     sa.Column('id', sa.ForeignKey(entities.c.id, ondelete='CASCADE'), primary_key=True),
#     sa.Column('type', sa.ForeignKey(entities.c.type, ondelete='CASCADE'), sa.CheckConstraint('type=comment'), nullable=False),
#     sa.Column('creator', sa.ForeignKey(entities.c.creator, ondelete='CASCADE'), nullable=False),
#     sa.Column('date_created', sa.DateTime(timezone=True), default=datetime.now()),
#     sa.Column('date_last_modified', sa.DateTime(timezone=True), default=datetime.now()),
#     sa.Column('text', sa.ForeignKey(entities.c.text, ondelete='CASCADE'), nullable=False),
#     sa.Column('parent_id', sa.Integer(), nullable=False),
# )


class RecordNotFound(Exception):
    """Custom exception for missing records."""


class ExecuteException(Exception):
    """Custom exception for failed executions."""


async def init_pg(app, env='dev'):
    """Init an app with aiopg engine."""
    conf = app['config'][env]['postgres']
    engine = await aiopg.sa.create_engine(
        database=conf['database'],
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        loop=app.loop)
    app['db'] = engine


async def close_pg(app):
    """Close the aiopg engine for the app."""
    app['db'].close()
    await app['db'].wait_closed()


async def db_get_comments(conn, username):
    """Get all the comments for a given user."""
    result = await conn.execute(
        """
        SELECT DISTINCT ON(id) *
        FROM comments, users 
        WHERE comments.creator = %s
        """,
        (username,)
    )

    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No comments found for  user {}'.format(username))


async def db_create_comment(conn, username, text, entity_id):
    """Create a new comment for a given entity."""
    try:
        await conn.execute(
            "INSERT INTO comments (type, creator, user_last_modified, text, parent_id)"
            "VALUES ('comment', %s, %s, %s, %s);",
            (username, username, text, entity_id)
        )
    except:
        res = await conn.execute(
            'SELECT * from entities limit 10'
        )
        entities = await res.fetchall()
        raise ExecuteException(
            'Failed to create the new comment, probably incorrect entity was provided.\n'
            '10 valid entities:\n{}'.format(' '.join(str(e.id) for e in entities))
        )


async def db_get_1lvl_comments(conn, entity_id, offset=0, limit=5):
    """
    Get all first-level children for the given entity,

    Uses pagination, so expects an offset and a limit.
    """
    result = await conn.execute(
        """
        SELECT * FROM comments WHERE parent_id = %s
        OFFSET %s LIMIT %s

        """,
        (entity_id, offset, limit)
    )
    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No comments found for entity {}'.format(entity_id))


async def db_change_comment(conn, user, comment_id, text):
    result = await conn.execute(
        """
        UPDATE comments
        SET text=%s, date_last_modified = %s, user_last_modified=%s
        WHERE id=%s
        """,
        (text, datetime.now(), user, comment_id)
    )
    try:
        return result
    except:
        raise ExecuteException('Failed to change the comment')


async def db_delete_comment(conn, user, comment_id):
    """
    Delete comment. Doesn't check permissions.

    Essentially, comment is NOT deleted(allowing further restore.)
    Thus, text is set to null.
    """
    # TODO cant delete if there're children
    result = await conn.execute(
        """
        UPDATE comments
        SET text=DEFAULT, date_last_modified = %s, user_last_modified=%s
        WHERE id=%s""",
        (datetime.now(), user, comment_id)
    )
    try:
        return result
    except:
        raise ExecuteException('Failed to delete the comment')


async def db_get_child_comments(conn, entity_id):
    """Get a list of children comments for a given entity."""
    result = await conn.execute(
        """
        SELECT S.id, S.creator, S.date_created, S.date_last_modified, S.text, S.parent_id
        FROM comments as S JOIN entities_closure_table as CT on S.id = CT.descendant_id 
        WHERE CT.ancestor_id=%s AND CT.descendant_id !=%s;
        """,
        (entity_id, entity_id)
    )
    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No comments found for entity {}'.format(entity_id))


async def db_get_full_tree(conn, root_id):
    """Get a full tree of comments for a given root."""
    result = await conn.execute(
        """
        SELECT S.id, S.creator, S.date_created, S.date_last_modified, S.text, S.parent_id
        FROM entities as S JOIN entities_closure_table as CT on S.id = CT.descendant_id 
        WHERE CT.ancestor_id=%s;
        """,
        (root_id,)
    )
    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No tree found for root {}'.format(root_id))



async def db_get_deleted_text(conn, user, entity_id):
    """
    Get removed text for a given entity.

    Since comments are not essentially removed(only test),
    it's possible to get text to restore later.
    """
    result = await conn.execute(
        """
        SELECT * FROM history
        WHERE entity_id=%s AND action='delete' --and "user"=%s TODO add and test
        ORDER BY date DESC limit 1
        """,
        (user, entity_id)
    )
    record = await result.first()
    if record:
        return record
    else:
        raise RecordNotFound('Could not find deleted comment[id={}]'.format(entity_id))


async def db_get_history(conn, user, start_date, end_date, root_comment_id):
    """
    Fetch a history of comments.

    Update search history for the further use.
    """
    start_date_condition = "AND date >= '{}'::date".format(start_date) if start_date else ""
    end_date_condition = "AND date <= '{}'::date".format(end_date) if end_date else ""
    root_comment_condition = "AND entity_id={}".format(root_comment_id) if root_comment_id else ""
    result = await conn.execute(
        """SELECT * FROM history WHERE "user"='{user}' {sdc} {edc} {rcc}""".format(
            user=user,
            sdc=start_date_condition,
            edc=end_date_condition,
            rcc=root_comment_condition
        ),
    )
    records = await result.fetchall()
    await conn.execute(
        """INSERT INTO search_history("user", "start_date", "end_date", "root_comment_id")
           VALUES (%s, %s, %s, %s)
        """,
        (user, start_date, end_date, root_comment_id)
    )

    if not records:
        raise RecordNotFound('No history found for the given parameters')
    return records


async def db_get_search_history(conn, user):
    """Get list of comment searches for the given user."""
    result = await conn.execute(
        """SELECT * from search_history WHERE "user"=%s""",
        (user,)
    )
    records = await result.fetchall()
    if not records:
        raise RecordNotFound
    return records
