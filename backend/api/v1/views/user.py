# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/04/06 下午4:01
# File: user.py
# IDE: PyCharm

from flask import g, jsonify, url_for, current_app, send_from_directory
from backend.api.v1 import api_v1
from backend.decorators import auth_required
from backend.api.v1.schemas import mytask_schema, users_schema
from backend.models import AnsibleTasks, User


@api_v1.route('/user/info', methods=['GET'])
@auth_required
def userinfo():
    return jsonify({
        "id": g.user.id,
        "name": g.user.username,
        "avatar": url_for("api_v1.get_avatar", filename=g.user.avatar_s, _external=True)
    })


@api_v1.route('/avatars/<path:filename>', methods=['GET'])
def get_avatar(filename):
    """用户头像"""
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)

@api_v1.route('/user/state', methods=['GET'])
@auth_required
def email_state():
    return jsonify({
        'is_active': g.user.confirmed
    })


@api_v1.route('/user/timeline', methods=['GET'])
@auth_required
def timeline():
    """用户最近发布的5个任务"""
    my_tasks = AnsibleTasks.query.filter_by(user=g.user).limit(5).all()
    return jsonify(mytask_schema(my_tasks))


@api_v1.route('/users', methods=['GET'])
@auth_required
def get_users():
    """用户列表接口"""
    users = User.query.all()
    return jsonify(users_schema(users))
