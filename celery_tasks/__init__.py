# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/2 下午8:21
# File: __init__.py
# IDE: PyCharm

from celery.utils.log import get_task_logger
from backend import create_app, make_celery
# from backend.extensions import celery_ext
celery_logger = get_task_logger(__name__)


app = create_app()
celery = make_celery(app)


class MyTask(celery.Task):  # 回调
    def on_success(self, retval, task_id, args, kwargs):
        celery_logger.info("执行成功 notice from on_success")
        return super(MyTask, self).on_success(retval, task_id, args, kwargs)

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        tid = kwargs.get("tid")
        tid = tid if tid else args[0]
        celery_logger.error("执行失败 notice from on_failure")
        print('{0!r} failed: {1!r}'.format(task_id, exc))
        return super(MyTask, self).on_failure(exc, task_id, args, kwargs, einfo)

    def on_retry(self, exc, task_id, args, kwargs, einfo):
        print(task_id, "任务重试")
        return super().on_retry(self, exc, task_id, args, kwargs, einfo)
