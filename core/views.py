"""Module to represent a list if views."""

from collections import namedtuple
from math import ceil
import json

from lxml import etree
from aiohttp import web
import aiohttp_jinja2

from db import *


Search = namedtuple('Search', ('search_date', 'start_date', 'end_date', 'root_comment_id'))
Action = namedtuple('Action', ('entity_id', 'user', 'action', 'date', 'text'))


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
        try:
            await db_get_1lvl_comments(conn, comment_id)
        except RecordNotFound:
            pass
        else:
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
            await db_change_comment(conn, user, comment_id, text)
        except (RecordNotFound, ExecuteException) as e:
            raise web.HTTPInternalServerError(text=str(e))
        return web.Response(
            text='comment[id={id}] was restored[text={text}]'.format(
                id=comment_id, text=text.text)
        )


async def get_child_comments(request):
    """Get child comments tree for the given comment ID."""
    entity_id = request.rel_url.query.get('entity_id')
    if not entity_id:
        raise web.HTTPBadRequest(text='ancestor entity id is missing')
    async with request.app['db'].acquire() as conn:
        try:
            comments = await db_get_child_comments(conn, entity_id)
        except ExecuteException as e:
            raise web.HTTPInternalServerError(text=str(e))
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))

        return web.json_response(text=json.dumps(comments.__repr__()))


async def get_full_tree(request):
    """Get child comments tree for the given comment ID."""
    root_id = request.rel_url.query.get('root_id')
    if not root_id:
        raise web.HTTPBadRequest(text='root_id is missing')
    async with request.app['db'].acquire() as conn:
        try:
            comments = await db_get_full_tree(conn, root_id)
        except ExecuteException as e:
            raise web.HTTPInternalServerError(text=str(e))
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))

        return web.json_response(text=json.dumps(comments.__repr__()))


def compose_history_in_xml(actions):
    """Compose xml output for the given history."""
    root = etree.Element('Actions')
    for action in actions:
        e_action = etree.SubElement(root, 'Action')
        for attr, val in action.items():
            sub = etree.SubElement(e_action, attr)
            sub.text = str(val)
    return etree.tostring(root, encoding='unicode')


async def get_history(request):
    """
    Return xml file with the history of comments.

    User has an option to specify comment UD and date range,
    default is all comments get returned.
    """
    data = await request.post()
    user = request.match_info['user']
    root_comment_id = data.get('comment_id') or None
    download_format = data['download_format']
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
    actions = [
        Action(
            a.entity_id,
            a.user,
            a.action,
            a.date.strftime('%Y-%m-%d %H:%M:%S'),
            a.text
        )._asdict() for a in result
    ]
    if download_format == 'json':
        output = json.dumps(actions)
    elif download_format == 'xml':
        output = compose_history_in_xml(actions)
    else:
        raise Exception('unsupported format {}'.format(download_format))
    filename = '{}_history.{}'.format(user, download_format)

    res = web.Response(
        text=output,
        headers={
            'Content-Type': 'application/octet-stream',
            'Content-Disposition': 'attachment; filename={}'.format(filename),
        }
    )
    await res.prepare(request)
    return res


@aiohttp_jinja2.template('history.html')
async def get_search_history(request):
    """
    Show the list of previous searches.

    Allow to re-download one.
    """
    user = request.match_info['user']
    async with request.app['db'].acquire() as conn:
        try:
            result = await db_get_search_history(conn, user)
        except RecordNotFound as e:
            raise web.HTTPNotFound(text=str(e))
        searches = [
            Search(res.search_date, res.start_date, res.end_date, res.root_comment_id)
            for res in result
        ]
        return {'searches': searches}
