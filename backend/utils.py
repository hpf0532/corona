# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:31
# File: utils.py
# IDE: PyCharm

import ipaddress, glob, os
from flask import jsonify, current_app
from werkzeug.http import HTTP_STATUS_CODES
from webargs import ValidationError
from backend.models import HostGroup
from backend.settings import playbook_dir
from backend.extensions import db


def validate_ip(val):
    try:
        ip = ipaddress.ip_address(val)
        if ip.is_loopback or ip.is_multicast or ip.is_reserved:
            raise ValueError
    except ValueError as e:
        raise ValidationError("非法的IP地址")


def validate_playbook(val):
    os.chdir(playbook_dir)
    file_list = glob.glob('*.y*ml')
    if val not in file_list:
        raise ValidationError("playbook文件不存在")


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


def model_to_dict(result):
    from collections import Iterable
    # 转换完成后，删除  '_sa_instance_state' 特殊属性
    try:
        if isinstance(result, Iterable):
            tmp = [dict(zip(res.__dict__.keys(), res.__dict__.values())) for res in result]
            for t in tmp:
                t.pop('_sa_instance_state')
        else:
            tmp = dict(zip(result.__dict__.keys(), result.__dict__.values()))
            tmp.pop('_sa_instance_state')
        return tmp
    except BaseException as e:
        print(e.args)
        raise TypeError('Type error of parameter')
