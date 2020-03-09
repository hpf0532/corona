# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午9:48
# File: schemas.py
# IDE: PyCharm

from flask import url_for


def host_schema(host):
    return {
        'id': host.id,
        'kind': 'Host',
        'self': url_for('api_v1.host', host_id=host.id, _external=True),
        'hostname': host.hostname,
        'ip': host.ip,
        'port': host.port,
        'group': host.group.name if host.group else None
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


def groups_schema(items):
    return {
        'self': url_for('api_v1.groups', _external=True),
        'kind': 'GroupCollection',
        'items': [group_schema(item) for item in items],
        'count': len(items)
    }