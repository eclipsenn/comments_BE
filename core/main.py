from aiohttp import web
import aiohttp_jinja2
import asyncio
import jinja2

from routes import setup_routes
from settings import config
from db import close_pg, init_pg


loop = asyncio.get_event_loop()
app = web.Application(loop=loop)
app['config'] = config

# setup Jinja2 template renderer
# since we're running from core package, just point on templates
aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('templates', ''))

setup_routes(app)
# create connection to the database
app.on_startup.append(init_pg)
# shutdown db connection on exit
app.on_cleanup.append(close_pg)
web.run_app(app, port=8080)
