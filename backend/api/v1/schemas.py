# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午9:48
# File: schemas.py
# IDE: PyCharm
import json
from flask import url_for


def host_schema(host):
    return {
        'id': host.id,
        'kind': 'Host',
        'self': url_for('api_v1.host', host_id=host.id, _external=True),
        'hostname': host.hostname,
        'ip': host.ip,
        'port': host.port,
        'group': host.group.id if host.group else None
    }


def hosts_schema(items, current, prev, next, pagination):
    return {
        'self': current,
        'kind': 'HostCollection',
        'items': [host_schema(item) for item in items],
        'prev': prev,
        'first': url_for('api_v1.hosts', page=1, _external=True),
        'last': url_for('api_v1.hosts', page=pagination.pages, _external=True),
        'next': next,
        'count': pagination.total
    }


def group_schema(group):
    return {
        'id': group.id,
        'kind': 'HostGroup',
        'self': url_for('api_v1.group', group_id=group.id, _external=True),
        'name': group.name,
        'description': group.description
    }


def groups_schema(groups):
    return {
        'self': url_for('api_v1.groups', _external=True),
        'kind': 'GroupCollection',
        'items': [group_schema(item) for item in groups],
        'count': len(groups)
    }


def playbook_schema(playbook):
    return {
        'id': playbook.id,
        'kind': 'PlayBook',
        'self': url_for('api_v1.playbook', playbook_id=playbook.id, _external=True),
        'name': playbook.name,
        'author': playbook.author,
        'information': playbook.information,
    }


def play_detail_schema(playbook):
    return {
        'id': playbook.id,
        'kind': 'PlayBook',
        'self': url_for('api_v1.playbook', playbook_id=playbook.id, _external=True),
        'name': playbook.name,
        'author': playbook.author,
        'information': playbook.information,
        'detail': playbook.detail.content
    }


def playbooks_schema(playbooks):
    return {
        'self': url_for('api_v1.playbooks', _external=True),
        'kind': 'PlayBookCollection',
        'items': [playbook_schema(item) for item in playbooks],
        'count': len(playbooks)
    }


def task_schema(task):
    return {
        'id': task.id,
        'kind': 'Task',
        'self': url_for('api_v1.task', task_id=task.id, _external=True),
        'ansible_id': task.ansible_id,
        'aplaybook': task.playbook,
        'state': task.state,
        'create_time': int(task.create_time.timestamp())
    }


def task_detail_schema(task):
    return {
        'id': task.id,
        'kind': 'TaskDetail',
        'self': url_for('api_v1.task', task_id=task.id, _external=True),
        'ansible_id': task.ansible_id,
        'celery_id': task.celery_id,
        'extra_vars': json.loads(task.extra_vars),
        'ansible_result': json.loads(task.ansible_result),
        'celery_result': json.loads(task.celery_result),
        'playbook': task.playbook,
        'state': task.state,
        'create_time': int(task.create_time.timestamp())
    }


def tasks_schema(items, current, prev, next, pagination):
    return {
        'self': current,
        'kind': 'TaskCollection',
        'items': [task_schema(item) for item in items],
        'prev': prev,
        'first': url_for('api_v1.tasks', page=1, _external=True),
        'last': url_for('api_v1.tasks', page=pagination.pages, _external=True),
        'next': next,
        'count': pagination.total
    }
