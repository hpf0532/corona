import json
import datetime
import random, string
from flask import g
from backend.models import AnsibleTasks
from celery_tasks.tasks import sync_ansible_result, ansible_playbook_exec, ansible_exec, error_handler
from backend.extensions import db


class AnsibleOpt:
    @staticmethod
    def ansible_playbook(hosts, playbook, option, user=None, extra_vars={}, **kw):
        # 调用 celery 的 ansiblePlayBook 任务，将任务推送给 celery 并写入 db
        tid = "AnsibleApiPlaybook-%s-%s" % (''.join(random.sample(string.ascii_letters + string.digits, 8)),
                                            datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
        # if not extra_vars.get('groupName'):
        #     extra_vars['groupName'] = groupName
        celery_task = ansible_playbook_exec.apply_async(
            (tid, hosts, playbook, extra_vars), link=sync_ansible_result.s(tid=tid),
            link_error=error_handler.s()
        )  # 保存 ansible 结果
        # print(tid, celery_task.task_id, extra_vars, playbook, "===========")
        at = AnsibleTasks(
            ansible_id=tid,
            celery_id=celery_task.task_id,
            user=g.user,
            extra_vars=json.dumps(extra_vars),
            playbook=playbook,
            option_id=option
        )
        db.session.add(at)
        db.session.commit()
        return {
            "playbook": playbook,
            "extra_vars": extra_vars,
            "ansible_id": tid,
            "celery_task": celery_task.task_id,
            "pk": at.id
        }

    @staticmethod
    def ansible_opt():
        tid = "AnsibleApiOpt-%s" % datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        tasks = []
        celery_task = ansible_exec.delay(tid, tasks)
        return {'tid': tid,
                'celery_task': celery_task.task_id,
                }



