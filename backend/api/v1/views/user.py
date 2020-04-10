# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/04/06 下午4:01
# File: user.py
# IDE: PyCharm

from flask import g, jsonify, url_for, current_app, send_from_directory
from backend.api.v1 import api_v1
from backend.decorators import auth_required


@api_v1.route('/user/info', methods=['GET'])
@auth_required
def userinfo():
    return jsonify({
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
