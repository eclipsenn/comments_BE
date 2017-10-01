"""
Base testing module with fixtures and utilies for async testing.

pytest-asyncio is a plugin with a bunch of useful fixtures,
not well-documented yet though.
Main things to remember of:
 - event_loop is redefined to be session-scoped;
 - if exception is raised during setup then finalizer
    won't be called. So need to add finaliser explicitly,
    (see `init_a_few_db_entries`) or handle exceptions gracefully
    during setup.
"""

import aiofiles
import aiopg.sa
import aiohttp_jinja2
import jinja2
import pytest
from aiohttp import web
from aiohttp.test_utils import loop_context

from routes import setup_routes
from settings import config


@pytest.fixture(scope='session')
def loop():
    """Event loop fixture, session-scoped."""
    with loop_context() as _loop:
        yield _loop

@pytest.yield_fixture(scope='session')
def event_loop(loop):
    """
    This is needed for correct functioning of the test_client of
    aiohttp together with pytest.mark.asyncio pytest-asyncio
    decorator. For more info check the following link:
    https://github.com/KeepSafe/aiohttp/issues/939
    """
    loop._close = loop.close
    loop.close = lambda: None
    yield loop


@pytest.fixture(scope='session')
async def comments_app():
    """App fixture, with db engine set up."""
    _app = web.Application()
    _app['config'] = config
    # fill route table
    setup_routes(_app)
    # setup template engine
    aiohttp_jinja2.setup(_app, loader=jinja2.PackageLoader('templates', ''))
    # setup testDB connection
    conf = _app['config']['test']['postgres']
    engine = await aiopg.sa.create_engine(
        database='test_comments_db',
        user=conf['user'],
        password=conf['password'],
        host=conf['host'],
        port=conf['port'],
        minsize=conf['minsize'],
        maxsize=conf['maxsize'],
        loop=_app.loop)
    _app['db'] = engine

    yield _app

    _app['db'].close()
    await _app['db'].wait_closed()


@pytest.fixture
def app():
    """
    Simple app fixture with config setup.

    TODO: remove if not used anywhere besides db connection test.
    """
    _app = web.Application()
    _app['config'] = config
    return _app


@pytest.fixture(scope='session')
async def conn(comments_app):
    """Connection fixture, session-scoped."""
    async with comments_app['db'].acquire() as _conn:
        yield _conn


@pytest.fixture
async def init_a_few_db_entries(request, conn, loop):
    """
    Populate tables with a few entries.

    Gets entries get cleaned for every test.
    """
    def finalizer():
        async def finalize():
            async with aiofiles.open('dbtools/init/1_clean.sql', 'r') as f:
                await conn.execute(await f.read())
        loop.run_until_complete(finalize())
    request.addfinalizer(finalizer)
    for setup_file in ('dbtools/init/2_create_tables.sql', 'dbtools/examples_a_few.sql'):
        async with aiofiles.open(setup_file, 'r') as f:
            await conn.execute(await f.read())