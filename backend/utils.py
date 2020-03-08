# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:31
# File: utils.py
# IDE: PyCharm

import ipaddress
from flask import jsonify, current_app
from werkzeug.http import HTTP_STATUS_CODES
from webargs import ValidationError
from backend.models import HostGroup
from backend.extensions import db


def validate_ip(val):
    try:
        ip = ipaddress.ip_address(val)
        if ip.is_loopback or ip.is_multicast or ip.is_reserved:
            raise ValueError
    except ValueError as e:
        raise ValidationError("非法的IP地址")


def validate_group_id(val):
    gid = HostGroup.query.get(val)
    if not gid:
        raise ValidationError("主机组不存在")


def api_abort(code, message=None, **kwargs):
    if message is None:
        message = HTTP_STATUS_CODES.get(code, '')
    response = jsonify(code=code, message=message, **kwargs)
    response.status_code = code
    return response
