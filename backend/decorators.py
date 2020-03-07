# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/5 下午4:57
# File: decorators.py
# IDE: PyCharm

import jwt
from flask import request, current_app, g
from jwt import ExpiredSignatureError
from functools import wraps
from backend.utils import api_abort
from backend.models import User


def auth_required(view):
    wraps(view)

    def wrapper(*args, **kwargs):
        token = request.headers.get('Auth-Jwt')
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
        except Exception as e:
            current_app.logger.error(e)
            return api_abort(401, "token非法")

        # 执行视图函数
        return view(*args, **kwargs)

    return wrapper