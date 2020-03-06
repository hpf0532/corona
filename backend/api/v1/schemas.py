# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午9:48
# File: schemas.py
# IDE: PyCharm

from flask import url_for


def group_schema(group):
    return {
        'id': group.id,
        'kind': 'HostGroup',
        # 'self': url_for()
        'name': group.name,
        'description': group.description
    }

def groups_schema(items, current, prev, next, pagination):
    return {
        'self': current,
        'kind': 'GroupCollection',
        'items': [group_schema(item) for item in items],
        'prev': prev,
        'first': url_for('api_v1.groups', page=1, _external=True),
        'last': url_for('api_v1.groups', page=pagination.pages, _external=True),
        'next': next,
        'count': pagination.total
    }