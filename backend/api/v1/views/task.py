# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/10 下午4:01
# File: task.py
# IDE: PyCharm

from flask import request, jsonify, current_app, url_for
from flask.views import MethodView
from backend.api.v1 import api_v1
from backend.models import Host, PlayBook, AnsibleTasks
from backend.utils import api_abort
from backend.api.v1.schemas import tasks_schema, task_detail_schema
from ansible_index import AnsibleOpt


class TaskAPI(MethodView):
    def get(self, task_id):
        task = AnsibleTasks.query.get_or_404(task_id)
        return jsonify(task_detail_schema(task))


class TasksAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        """分页获取task任务列表"""
        page = request.args.get('page', 1)
        per_page = current_app.config['BACK_ITEM_PER_PAGE']
        pagination = AnsibleTasks.query.paginate(page, per_page)
        items = pagination.items
        current = url_for('.tasks', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.tasks', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.tasks', page=page + 1, _external=True)

        print(items)
        return jsonify(tasks_schema(items, current, prev, next, pagination))

    def post(self):
        """提交任务接口"""
        print(request.json)
        exec_hosts = []
        payload = request.json
        hosts = Host.query.filter(Host.id.in_(payload["hosts"])).all()
        print(hosts)
        if not hosts:
            return api_abort(400, "参数有误")
        for host in hosts:
            exec_hosts.append((host.ip, host.port))

        playbook = PlayBook.query.get_or_404(payload['playbook'])
        playbook = playbook.name
        extra_vars = payload["extra_vars"]
        print(extra_vars)
        print(playbook)

        print(exec_hosts)

        ret = AnsibleOpt.ansible_playbook(exec_hosts, playbook, extra_vars=extra_vars)

        return jsonify(ret)


api_v1.add_url_rule('/tasks', view_func=TasksAPI.as_view('tasks'), methods=['GET', 'POST'])
api_v1.add_url_rule('/tasks/<int:task_id>', view_func=TaskAPI.as_view('task'), methods=['GET'])
