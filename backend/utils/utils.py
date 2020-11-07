# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:31
# File: utils.py
# IDE: PyCharm

import datetime
import ipaddress, glob, json, os, jwt
import random
import redis

import bcrypt
from jwt import ExpiredSignatureError, InvalidTokenError
from flask import jsonify, current_app
from werkzeug.http import HTTP_STATUS_CODES
from webargs import ValidationError
from backend.models import HostGroup, PlayBook, Environment, Category
from backend.settings import playbook_dir, Operations, POOL
from backend.extensions import db, redis_conn

def isAlnum(word):
    """
    判断字符串为字母和数字组成，排除中文
    :param word:
    :return:
    """
    try:
        return word.encode('ascii').isalnum()
    except UnicodeEncodeError:
        return False

def gen_token(user, operation, expire_in=None, **kwargs):
    """
    生成token函数
    :param operation: 操作类型
    :param expire_in: 超时时间
    :param user_id:
    :return:
    """
    if not expire_in:
        expire_in = current_app.config.get('AUTH_EXPIRE')
    data = {
        "user_id": user.id,
        "operation": operation,
        "exp": int(datetime.datetime.now().timestamp()) + expire_in  # 超时时间
    }
    data.update(**kwargs)
    token = jwt.encode(data, current_app.config.get("SECRET_KEY"), 'HS256').decode()

    return token


def validate_token(user, token, operation, new_password=None):
    """验证token"""
    try:
        data = jwt.decode(token, current_app.config.get("SECRET_KEY"), algorithms=['HS256'])
    except (ExpiredSignatureError, InvalidTokenError):
        return False

    if operation != data.get('operation') or user.id != data.get('user_id'):
        return False

    if operation == Operations.CONFIRM:
        user.confirmed = True
    elif operation == Operations.RESET_PASSWORD:
        user.password = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt())
    else:
        return False

    db.session.commit()
    return True


def validate_ip(val):
    """校验ip类型"""
    try:
        ip = ipaddress.ip_address(val)
        if ip.is_loopback or ip.is_multicast or ip.is_reserved:
            raise ValueError
    except ValueError as e:
        raise ValidationError("非法的IP地址")


def validate_json(val):
    """校验json格式"""
    try:
        print(val)
        json.loads(val)
    except ValueError:
        raise ValidationError("json格式错误")


def validate_playbook(val):
    """校验playbook文件是否存在"""
    os.chdir(playbook_dir)
    file_list = glob.glob('*.y*ml')
    if val not in file_list:
        raise ValidationError("playbook文件不存在")


def validate_group_id(val):
    gid = HostGroup.query.get(val)
    if not gid:
        raise ValidationError("主机组不存在")


def validate_playbook_id(val):
    pid = PlayBook.query.get(val)
    if not pid:
        raise ValidationError("playbook不存在")


def validate_env_id(val):
    pid = Environment.query.get(val)
    if not pid:
        raise ValidationError("环境参数错误")


def validate_category_id(val):
    cid = Category.query.get(val)
    if not cid:
        raise ValidationError("分类不存在")


def api_abort(code, message=None, **kwargs):
    if message is None:
        message = HTTP_STATUS_CODES.get(code, '')
    response = jsonify(code=code, message=message, **kwargs)
    response.status_code = code
    return response


def gen_captcha():
    """生成验证码函数"""
    tmp_list = []
    for i in range(4):
        u = chr(random.randint(65, 90))  # 大写字母
        l = chr(random.randint(97, 122))  # 小写字母
        n = str(random.randint(0, 9))  # 数字

        tmp = random.choice([u, l, n])
        tmp_list.append(tmp)

    return "".join(tmp_list), tmp_list


def get_random_color():
    """定义随机获取颜色的函数"""
    return random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)


def validate_capcha(cap_id, user_cap):
    """验证用户输入的验证码"""
    capcha = redis_conn.get(cap_id)
    print(capcha.decode())
    if not capcha: return False
    if user_cap.lower() == capcha.decode():
        return True
    else:
        return False


def get_task_progress(task_obj):
    """获取任务执行进度"""
    percentage = 0
    total_step = PlayBook.query.filter(PlayBook.name == task_obj.playbook).first().step
    progress = True if total_step else False
    # 已完成的任务进度为100
    if task_obj.status.val == 2:
        percentage = 100
        return progress, percentage
    # 获取未完成的任务
    over_task_count = redis_conn.llen(task_obj.ansible_id)
    if total_step:
        percentage = round((over_task_count / total_step) * 100)

    return progress, percentage


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
