# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/5 下午4:57
# File: decorators.py
# IDE: PyCharm

import jwt, redis
from flask import request, current_app, g
from jwt import ExpiredSignatureError
from functools import wraps
from backend.utils.utils import api_abort
from backend.models import User
from backend.settings import POOL, Operations
from backend.extensions import redis_conn


# 判断元素是否在有序集合中
def zexist(name, value):
    index = redis_conn.zrank(name, value)
    # print(index)
    if index == 0 or index:
        return True
    return False


def auth_required(view):
    """登录保护装饰器"""

    @wraps(view)
    def wrapper(*args, **kwargs):
        token = request.headers.get('X-Token')

        # 没有token
        if not token:
            return api_abort(401, "token缺失")

        # 黑名单token
        if zexist("token_blacklist", token):
            return api_abort(401, "token非法")

        # 验证token
        try:
            data = jwt.decode(token, current_app.config.get("SECRET_KEY"), algorithms=['HS256'])
        except ExpiredSignatureError as e:
            current_app.logger.error("token超时: {}".format(e))
            return api_abort(401, "token超时")
        except Exception as e:
            current_app.logger.error("token非法: {}".format(e))
            return api_abort(401, "token非法")

        # 验证token类型为LOGIN
        if data.get('operation') != Operations.LOGIN:
            return api_abort(401, "token非法")

        # token验证通过，将当前用户挂载到g变量中
        try:
            user_id = data.get("user_id", -1)
            user = User.query.filter_by(id=user_id).one()
            g.user = user
            g.token = token
        except Exception as e:
            current_app.logger.error(e)
            return api_abort(401, "token非法")

        # 执行视图函数
        return view(*args, **kwargs)

    return wrapper


def confirm_required(view):
    """邮箱确认装饰器"""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not g.user.confirmed:
            return api_abort(403, "您的邮箱未认证")
        return view(*args, **kwargs)

    return wrapper


def check_stoken(view):
    """保证接口幂等"""

    @wraps(view)
    def wrapper(*args, **kwargs):
        stoken = request.args.get("stoken")
        if not stoken:
            return api_abort(403, "stoken缺失")

        stoken_key = str(g.user.username) + "_stoken"
        save_token = redis_conn.get(stoken_key)
        # print(save_token.decode(), stoken)
        if not save_token:
            return api_abort(403, "请勿重复操作")
        if stoken != save_token.decode():
            return api_abort(403, "stoken校验失败")

        redis_conn.delete(stoken_key)

        return view(*args, **kwargs)

    return wrapper


if __name__ == '__main__':
    a = zexist('token_blacklist',
               ".eyJ1c2VyX2lkIjoyLCJleHAiOjE1ODQwNDczOTB9.DtOY3brHem0hijulzl5sGc651gl29gBU6xRQOOh0KDs")
    print(a)
