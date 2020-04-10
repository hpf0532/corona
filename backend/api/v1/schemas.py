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
        'is_env': playbook.is_env
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
        'playbook': task.playbook,
        'user': task.user.username if task.user else None,
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
        'user': task.user.username if task.user else None,
        'extra_vars': json.loads(task.extra_vars) if task.extra_vars else None,
        'ansible_result': json.loads(task.ansible_result) if task.ansible_result else None,
        'celery_result': json.loads(task.celery_result) if task.celery_result else None,
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


def mytask_schema(items):
    return {
        'self': url_for('api_v1.timeline', _external=True),
        'kind': 'MyTaskCollection',
        'items': [task_schema(item) for item in items],
        'count': len(items)

    }


def flush_task_schema(task):
    return {
        'ansible_result': json.loads(task.ansible_result) if task.ansible_result else None,
        'celery_result': json.loads(task.celery_result) if task.celery_result else None,
    }


def host_group_schema(hosts):
    host_list = []
    for host in hosts:
        host_list.append(
            {
                "host_id": host.id,
                "hostname": host.hostname
            }
        )
    return host_list


def option_schema(option):
    return {
        'id': option.id,
        'kind': 'Option',
        'self': url_for('api_v1.option', option_id=option.id, _external=True),
        'name': option.name,
        'content': option.content,
        'playbook': option.playbook.id if option.playbook else None,
        'env': option.env.id if option.env else None
    }


def options_schema(items, current, prev, next, pagination):
    return {
        'self': current,
        'kind': 'OptionCollection',
        'items': [option_schema(item) for item in items],
        'prev': prev,
        'first': url_for('api_v1.options', page=1, _external=True),
        'last': url_for('api_v1.options', page=pagination.pages, _external=True),
        'next': next,
        'count': pagination.total
    }


def task_options_schema(items):
    return {
        'self': url_for('api_v1.task_options', _external=True),
        'kind': 'TaskOptionsCollection',
        'items': [option_schema(item) for item in items],
        'count': len(items)
    }


def env_schema(env):
    """环境信息"""
    return {
        'id': env.id,
        'kind': 'Env',
        'name': env.name,
    }


def envs_schema(envs):
    return {
        'self': url_for('api_v1.envs', _external=True),
        'kind': 'EnvCollection',
        'items': [env_schema(item) for item in envs],
        'count': len(envs)
    }
