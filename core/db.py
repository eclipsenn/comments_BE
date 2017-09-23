import aiopg.sa

# TODO: ORM is not implemented but quite possible to be
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
#     ancestor_id = sa.Column(sa.Integer(), sa.CheckConstraint('ancestor_id is NULL'))
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
#     ancestor_id = sa.Column(sa.Integer())
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
#     sa.Column('ancestor_id', sa.Integer()),
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
#     sa.Column('ancestor_id', sa.Integer(), nullable=False),
# )


class RecordNotFound(Exception):
    """Custom exception for missing records."""


class ExecuteException(Exception):
    """Custom exception for failed executions."""


async def init_pg(app):
    conf = app['config']['postgres']
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
    app['db'].close()
    await app['db'].wait_closed()


async def db_get_comments(conn, username):
    # result = await conn.execute(
    #     comments.select().where(comments.c.creator == username)
    # )
    result = await conn.execute(
        "SELECT DISTINCT ON(id) "
        "* FROM comments, users "
        "WHERE comments.creator = '{}'".format(username)
    )

    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No comments found for  user {}'.format(username))


async def db_create_comment(conn, username, text, entity_id):
    try:
        result = await conn.execute(
            "INSERT INTO comments (type,creator, user_last_modified, text,ancestor_id)"
            "VALUES ('comment', '{username}', '{username}',  '{text}', '{ancestor_id}');".format(
                username=username,
                text=text,
                ancestor_id=entity_id
            )
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
    return result



async def db_get_1lvl_comments(conn, entity_id, offset, limit):
    result = await conn.execute(
        """
        SELECT * FROM comments WHERE ancestor_id = %s
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
        "UPDATE comments "
        "SET text='{text}', date_last_modified = '{date}', user_last_modified='{user}' "
        "WHERE id='{id}'".format(text=text, date=datetime.now(), id=comment_id, user=user)
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
    result = await conn.execute(
        "UPDATE comments "
        "SET text=DEFAULT, date_last_modified = '{date}', user_last_modified='{user}' "
        "WHERE id='{id}'".format(date=datetime.now(), id=comment_id, user=user)
    )
    try:
        return result
    except:
        raise ExecuteException('Failed to delete the comment')


async def db_get_child_comments(conn, entity_id, with_root):
    db = 'entities' if with_root else 'comments'
    column = 'id' if with_root else 'ancestor_id'
    result = await conn.execute("""
        WITH RECURSIVE r as (
            SELECT id, creator, date_created, date_last_modified, text, ancestor_id
            FROM {db}
            WHERE "{column}"='{entity_id}'

            UNION

            SELECT comments.id, comments.creator, comments.date_created,
            comments.date_last_modified, comments.text, comments.ancestor_id
            FROM r JOIN comments on comments.ancestor_id = r.id
        )
        SELECT * FROM r;
    """.format(db=db, column=column, entity_id=entity_id))
    comments_record = await result.fetchall()
    if comments_record:
        return comments_record
    else:
        raise RecordNotFound('No comments found for entity {}'.format(entity_id))


async def db_get_deleted_text(conn, user, entity_id):
    result = await conn.execute(
        """SELECT * FROM history
        WHERE entity_id='{entity_id}' AND action='delete' --and "user"='{user}' TODO add and test
        ORDER BY date DESC limit 1""".format(
            user=user, entity_id=entity_id)
    )
    record = await result.first()
    if record:
        return record
    else:
        raise RecordNotFound('Could not find deleted comment[id={}]'.format(entity_id))


async def db_get_history(conn, user, start_date, end_date, root_comment_id):
    """
    Fetch an xml file with history of comments.

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
    """Get list of comment searches for the fiven user."""
    result = await conn.execute(
        """SELECT * from search_history WHERE "user"=%s""",
        (user,)
    )
    records = await result.fetchall()
    if not records:
        raise RecordNotFound
    return records