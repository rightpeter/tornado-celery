import os
import time
import json
from datetime import datetime

from celery import Celery
from celery import Task
from celery.utils import cached_property

import asyncio
import aioredis

celery = Celery("tasks")
celery.conf.broker_url = 'redis://localhost:6379/0'
celery.conf.result_backend = 'redis://'

class BaseTask(Task):
    abstract = True

    @cached_property
    def loop(self):
        return asyncio.get_event_loop()

    @cached_property
    def pool(self):
        return self.loop.run_until_complete(aioredis.create_redis_pool(
            'redis://localhost'))


    def get_channel_name(self, task_id):
        return str(task_id)

    def after_return(self, status, retval, task_id, args, kwargs, einfo):
        if status == 'FAILURE':
            retval = str(retval)

        ret_obj = {
            'status': status,
            'retval': retval,
            'task_id': task_id,
            'args': args,
            'kwargs': kwargs,
            'einfo': einfo
        }
        self.loop.run_until_complete(self.pool.publish_json(self.get_channel_name(task_id), ret_obj))


@celery.task(base=BaseTask)
def add(x, y):
    return int(x) + int(y)


@celery.task(base=BaseTask)
def sleep(seconds):
    time.sleep(float(seconds))
    return seconds


@celery.task(base=BaseTask)
def echo(msg, timestamp=False):
    return "%s: %s" % (datetime.now(), msg) if timestamp else msg


@celery.task(base=BaseTask)
def error(msg):
    raise Exception(msg)


if __name__ == "__main__":
    celery.start()
