# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/5 下午4:57
# File: decorators.py
# IDE: PyCharm

import jwt, redis
from flask import request, current_app, g
from jwt import ExpiredSignatureError
from functools import wraps
from backend.utils import api_abort
from backend.models import User
from backend.settings import POOL

conn = redis.Redis(connection_pool=POOL)

# 判断元素是否在有序集合中
def zexist(name, value):
    index = conn.zrank(name, value)
    print(index)
    if index == 0 or index:
        return True
    return False


def auth_required(view):
    wraps(view)

    def wrapper(*args, **kwargs):
        token = request.headers.get('X-Token')
        print(token)
        # 黑名单token
        if zexist("token_blacklist", token):
            return api_abort(401, "token非法")

        # 没有token
        if not token:
            return api_abort(401, "token缺失")

        # 验证token
        try:
            data = jwt.decode(token, current_app.config.get("SECRET_KEY"), algorithms=['HS256'])
        except ExpiredSignatureError as e:
            current_app.logger.error("token超时: {}".format(e))
            return api_abort(401, "token超时")
        except Exception as e:
            current_app.logger.error("token非法: {}".format(e))
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


if __name__ == '__main__':
    a = zexist('token_blacklist',
               ".eyJ1c2VyX2lkIjoyLCJleHAiOjE1ODQwNDczOTB9.DtOY3brHem0hijulzl5sGc651gl29gBU6xRQOOh0KDs")
    print(a)
