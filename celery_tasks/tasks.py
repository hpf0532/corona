import datetime
import os
import sys
import time

if os.getenv("PYTHONOPTIMIZE", ""):
    # print("开始启动")
    pass
else:
    print("\33[31m环境变量问题，Celery Client启动后无法正常执行Ansible任务，\n请设置export PYTHONOPTIMIZE=1；\n\33[32m程序退出\33[0m")
    sys.exit()
import redis
import requests
import json
from flask import current_app, render_template
from flask_mail import Message
from backend.settings import REDIS_ADDR, REDIS_PD, REDIS_PORT, ansible_result_redis_db, result_db, inventory, \
    DINGDING_URL, DINGDING_CONTACTS
from backend.extensions import mail
from celery.utils.log import get_task_logger
from celery.result import AsyncResult
from sqlalchemy.orm.exc import NoResultFound
from backend.utils.dingding import dingding_sign

celery_logger = get_task_logger(__name__)
# 导入 ansible api
from ansible_api import ansible_playbook_api, ansible_exec_api
from backend.models import AnsibleTasks
from backend.extensions import db
from backend.settings import BaseConfig, POOL
from celery_tasks import celery, MyTask

sources = inventory


def save_to_db(tid):
    r = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=ansible_result_redis_db)
    a = redis.Redis(host=REDIS_ADDR, password=REDIS_PD, port=REDIS_PORT, db=result_db)
    rlist = r.lrange(tid, 0, -1)
    query = db.session.query(AnsibleTasks)
    try:
        at = query.filter(AnsibleTasks.ansible_id == tid).one()
    except NoResultFound as e:
        at = query.filter(AnsibleTasks.celery_id == tid).one()

    at.ansible_result = json.dumps([json.loads(i.decode()) for i in rlist])
    ct = a.get('celery-task-meta-%s' % at.celery_id).decode()
    at.celery_result = ct
    at.state = True
    try:
        db.session.add(at)
        db.session.commit()
        return at
    except Exception as e:
        db.session.rollback()
        celery_logger.error("保存数据失败, 失败原因: {}".format(e))
        raise


@celery.task(bind=True, base=MyTask)
def error_handler(self, uuid):
    result = AsyncResult(uuid)
    # print(result.get())
    save_to_db(uuid)
    send_dingding_msg.apply_async()
    exc = result.get(propagate=False)
    print('Task {0} 抛出异常 exception: {1!r}\n{2!r}'.format(uuid, exc, result.traceback))
    return {"uuid": uuid}


@celery.task(bind=True, base=MyTask)    # bind=True 用于将自身信息传入函数
def sync_ansible_result(self, ret, *a, **kw):  # 执行结束，结果保持至db
    try:
        c = AsyncResult(self.request.get('parent_id'))  # 获取父任务 id
        cid = self.request.get('parent_id')
        celery_logger.info(c.result)
        tid = kw.get('tid', None)
        # celery_logger.info("+++++++++++"+str(self.request.get('parent_id')))
        # celery_logger.info("------------ %s" % current_app.name)
        if tid:
            task_obj = save_to_db(tid)
            data_dict = {
                "user": task_obj.user.username,
                "option": task_obj.option.name if task_obj.option else "",
                "playbook": task_obj.playbook,
                "create_time": task_obj.create_time,
                "ansible_id": task_obj.ansible_id,
                "validate_url": task_obj.option.url if task_obj.option else ""
            }
            send_dingding_msg.apply_async((data_dict,))
        else:
            pass
        # raise ValueError("测试失败")
    except Exception as e:
        db.session.rollback()
        celery_logger.error("保存ansible数据失败, 失败原因: {}".format(e))
        raise RuntimeError("保存ansible数据失败, 失败原因: {}".format(e))


# AnsibleApi 函数需要 5 个参数
@celery.task
def ansible_exec(tid, groupname, tasks=[], extra_vars={}):
    ansible_exec_api(tid, groupname, tasks, sources, extra_vars)
    return 'success'


# AnsiblePlaybookApi 函数需要 5 个参数
@celery.task(bind=True, base=MyTask)
def ansible_playbook_exec(self, tid, hosts, playbook, extra_vars={}):
    ansible_playbook_api(tid, hosts, ["playbooks/%s" % playbook], sources, extra_vars)
    return 'success'


# 删除过期token定时任务
@celery.task(bind=True, base=MyTask)
def flush_token(self):
    print(datetime.datetime.now())
    now = datetime.datetime.now().timestamp()
    expire = BaseConfig.AUTH_EXPIRE
    conn = redis.Redis(connection_pool=POOL)
    conn.zremrangebyscore("token_blacklist", 0, now - expire)
    return 'success'


# 发送邮件
@celery.task(bind=True, base=MyTask)
def send_mail(self, to, subject, template, **kwargs):
    message = Message(current_app.config['MAIL_SUBJECT_PREFIX'] + subject, recipients=[to])
    message.body = render_template(template + '.txt', **kwargs)
    message.html = render_template(template + '.html', **kwargs)
    mail.send(message)
    return "success"


@celery.task(bind=True, base=MyTask)
def send_dingding_msg(self, task_obj=None):
    """
    发送钉钉通知
    :param self:
    :param task_obj:
    :return:
    """
    headers = {'Content-Type': 'application/json;charset=utf-8'}
    if task_obj:
        msg = " 任务{playbook}发布完成\n 项目名称: {option}\n 发布人员: {user}\n 任务提交时间: {create_time}\n 任务ID: {ansible_id}\n 项目链接: {validate_url}\n ".format(
            **task_obj)
    else:
        msg = " 任务发布失败， 请登录系统查看，或联系管理员"
    json_text = {
        "msgtype": "text",
        "at": {
            "atMobiles": DINGDING_CONTACTS,
            "isAtAll": True
        },
        "text": {
            "content": msg
        }
    }
    timestamp, sign = dingding_sign()
    url = DINGDING_URL + "&timestamp=" + timestamp + "&sign=" + sign

    r = requests.post(url, json.dumps(json_text), headers=headers).content
    celery_logger.info(r.decode('utf-8'))
    return 'success'


# 测试任务
@celery.task(bind=True, base=MyTask)
def add(self, x, y):
    tid = "Test-%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    a = AnsibleTasks(ansible_id="123")
    db.session.add(a)
    celery_logger.info("11111111111 %s" % current_app.name)
    db.session.commit()
    current_app.logger.info("I have the application context")

    return x + y



