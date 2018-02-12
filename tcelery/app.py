from __future__ import absolute_import

import celery

import aioredis

from tornado import ioloop
from tornado import web
from tornado.options import define, options

from . import handlers as _  # noqa
from .utils import route


define("debug", type=bool, default=False, help="run in debug mode")


class Application(web.Application):
    def __init__(self, celery_app=None):
        # Prepare IOLoop class to run instances on asyncio
        ioloop.IOLoop.configure('tornado.platform.asyncio.AsyncIOMainLoop')
        handlers = route.get_routes()
        settings = dict(debug=options.debug)
        super(Application, self).__init__(handlers, **settings)
        self.celery_app = celery_app or celery.Celery()

    def init_with_loop(self, loop):
        self.redis_pool = loop.run_until_complete(
                aioredis.create_pool('redis://localhost', loop=loop)
        )
