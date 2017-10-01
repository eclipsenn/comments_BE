from datetime import datetime
from math import ceil
import json
import xml

from aiohttp import web
import aiohttp_jinja2

from db import *


# TODO: different formats
# TODO: db injection handling
# TODO: docstrings
# TODO: edge cases handling
# TODO: switch to namedtuple

class Comment:
    def __init__(self, comment_id, ancestor_id, text):
        self.id = comment_id
        self.ancestor_id = ancestor_id
        self.text = text

    def __repr__(self):
        return '(id={}, parent={},text={})'.format(self.id, self.ancestor_id, self.text)


class Search:
    def __init__(self, search_date=None, start_date=None, end_date=None, root_comment_id=None):
        self.search_date = search_date
        self.start_date = start_date
        self.end_date = end_date
        self.root_comment_id = root_comment_id


def compose_comment_tree(comments):
    """
    Compose a dict for the given list of comments

    :param comments: tuple of (id, user, create_time, changed_time, text, parent_id)
    :return: dict {parent_id : [child_ids]}, where child_ids are also dicts.
    """
    # TODO: can be faster than O(n^2) ?
    cs = list(Comment(c.id, c.ancestor_id, c.text) for c in comments)
    tmp = {}
    for c in cs[::-1]:
        keys = list(tmp.keys())
        changed = False
        for child in keys[:]:
            if c.id == child.ancestor_id:
                changed = True
                if c not in tmp:
                    tmp[c] = {}
                tmp[c][child] = tmp[child]
                del tmp[child]
        if not changed:
            tmp[c] = {}
    return tmp


@aiohttp_jinja2.template('index.html')
def index(request):
    """Show API help."""
    pass


@aiohttp_jinja2.template('create_comment.html')
def create_comment_form(request):
    pass


@aiohttp_jinja2.template('change_comment.html')
def change_comment_form(request):
    pass


@aiohttp_jinja2.template('delete_comment.html')
def delete_comment_form(request):
    pass


@aiohttp_jinja2.template('restore_comment.html')
def restore_comment_form(request):
    pass


@aiohttp_jinja2.template('get_history.html')
def get_history_form(request):
    pass


async def create_comment(request):
    """Create comment for the given entity."""
    data = await request.post()
    text = data['text']
    entity_id = data['entity_id']
    user = request.match_info['user']
    async with request.app['db'].acquire() as conn:
        try:
            await db_create_comment(conn, user, text, entity_id)
        except ExecuteException as e:
            raise web.HTTPInternalServerError(text=str(e))
        return web.Response(text='added a comment: {}!'.format(text))


async def get_comments(request):
    """Get comments for the given user."""
    username = request.match_info['user']
    async with request.app['db'].acquire() as conn:
        try:
            comments = await db_get_comments(conn, username)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        return web.json_response(data=comments.__repr__())


@aiohttp_jinja2.template('lvl1_children.html')
async def get_1lvl_comments(request):
    """
    Get first level comments for the given entity.

    Paginate 5 comments/page by default(for demo purposes).
    Show links to 2 previous and 2 next pages.
    """
    pagination = 5
    entity_id = request.rel_url.query.get('entity_id')
    if not entity_id:
        raise web.HTTPBadRequest(text='entity_id is missing')
    page_num = int(request.rel_url.query.get('page') or 1)
    offset = max(0, (page_num - 3) * pagination)
    limit = min(25, (3 + page_num - 1) * pagination)
    async with request.app['db'].acquire() as conn:
        try:
            comments = await db_get_1lvl_comments(
                conn, entity_id, offset=offset, limit=limit)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        chunks = int(ceil(len(comments) / pagination))
        data = {
            max(0, page_num - 3) + i + 1: comments[i * pagination:(i + 1) * pagination]
            for i in range(chunks)
        }
        return {
            'entity_id': entity_id,
            'page': page_num,
            'user': request.match_info['user'],
            'data': data
        }


async def change_comment(request):
    """
    Change comment for the given comment ID.

    Currently any user can change since auth is not implemented.
    """
    data = await request.post()
    comment_id = data.get('comment_id')
    user = request.match_info['user']
    if not comment_id:
        raise web.HTTPBadRequest(text='comment id is missing')
    text = data.get('text')
    if not text:
        raise web.HTTPBadRequest(text='text is missing')
    async with request.app['db'].acquire() as conn:
        try:
            await db_change_comment(conn, user, comment_id, text)
        except ExecuteException as e:
            raise web.HTTPInternalServerError(text=str(e))
        return web.Response(
            text='new comment with id={id} was set to "{text}"'.format(
                id=comment_id, text=text)
        )


async def delete_comment(request):
    """
    Delete comment for the given comment ID.

    Currently any user can delete since auth is not implemented.
    """
    data = await request.post()
    comment_id = data.get('comment_id')
    user = request.match_info['user']
    if not comment_id:
        raise web.HTTPBadRequest(text='comment id is missing')
    async with request.app['db'].acquire() as conn:
        children = await db_get_1lvl_comments(conn, comment_id)
        if children:
            return web.HTTPBadRequest(text='Cannot delete if the comment has children')
        try:
            await db_delete_comment(conn, user, comment_id)
        except ExecuteException:
            raise web.HTTPInternalServerError(
                text='Oops, something went wrong.')
        return web.Response(
            text='comment[id={id}] was deleted"'.format(id=comment_id)
        )


async def restore_comment(request):
    """
    Restore comment for the given comment ID.

    Currently any user can restore since auth is not implemented.
    """
    data = await request.post()
    comment_id = data.get('comment_id')
    user = request.match_info['user']
    if not comment_id:
        raise web.HTTPBadRequest(text='comment id is missing')
    async with request.app['db'].acquire() as conn:
        try:
            text = await db_get_deleted_text(conn, user, comment_id)
            await db_change_comment(conn, user, comment_id, text.text)
        except (RecordNotFound, ExecuteException) as e:
            raise web.HTTPInternalServerError(text=str(e))
        return web.Response(
            text='comment[id={id}] was restored[text={text}]'.format(
                id=comment_id, text=text.text)
        )


async def get_child_comments(request):
    """Get child comments tree for the given comment ID."""
    entity_id = request.rel_url.query.get('entity_id')
    with_root = 'true' == request.rel_url.query.get('with_root')
    if not entity_id:
        raise web.HTTPBadRequest(text='ancestor entity id is missing')
    async with request.app['db'].acquire() as conn:
        try:
            comments = await db_get_child_comments(conn, entity_id, with_root)
        except ExecuteException as e:
            raise web.HTTPInternalServerError(text=str(e))
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))

        data = compose_comment_tree(comments)
        return web.json_response(data=data.__repr__())


async def get_history(request):
    """
    Return xml file with the history of comments.

    User has an option to specify comment UD and date range,
    default is all comments get returned.
    """
    data = await request.post()
    user = request.match_info['user']
    root_comment_id = data.get('comment_id') or None
    start_date = data.get('start_date')
    if start_date in ('', 'None'):
        start_date = None
    end_date = data.get('end_date')
    if end_date in ('', 'None'):
        end_date = None
    try:
        async with request.app['db'].acquire() as conn:
            result = await db_get_history(conn, user, start_date, end_date, root_comment_id)
    except RecordNotFound as e:
        return web.Response(text=str(e))
    res = web.Response(
        body=bytes(json.dumps(result.__repr__()), encoding='utf8'),
        headers={
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment',
        }
    )
    await res.prepare(request)
    return res


@aiohttp_jinja2.template('history.html')
async def show_search_history(request):
    """
    Show the list of previous searches.

    Allow to re-download one.
    """
    user = request.match_info['user']
    async with request.app['db'].acquire() as conn:
        result = await db_get_search_history(conn, user)
    searches = [
        Search(res.search_date, res.start_date, res.end_date, res.root_comment_id)
        for res in result
    ]
    return {'searches': searches}
