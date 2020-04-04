# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/4 下午8:55
# File: auth.py
# IDE: PyCharm
import redis
import jwt, datetime, bcrypt
from flask import jsonify, request, current_app, g, send_from_directory, url_for
from sqlalchemy import or_
from backend.decorators import auth_required
from backend.utils import api_abort
from backend.api.v1 import api_v1
from backend.models import User
from backend.decorators import auth_required
from backend.extensions import db, avatars
from backend.settings import POOL


def gen_token(user_id):
    """
    生成token函数
    :param user_id:
    :return:
    """
    token = jwt.encode({
        "user_id": user_id,
        "exp": int(datetime.datetime.now().timestamp()) + current_app.config.get('AUTH_EXPIRE')   # 超时时间
    }, current_app.config.get("SECRET_KEY"), 'HS256').decode()

    return token


# 注册视图
@api_v1.route("/user/reg", methods=["POST"])
def register():
    payload = request.json

    try:  # 有任何异常，都返回400，如果保存数据出错，则向外抛出异常
        email = payload['email']
        username = payload['username']

        user = User.query.filter(or_(User.username == username, User.email == email)).first()
        if user:
            return api_abort(400, "用户已注册")

        password = payload['password']
        user = User(username=username, email=email)
        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        db.session.add(user)
        try:
            db.session.commit()
            current_app.logger.info("用户{}注册成功".format(username))
            return jsonify({"user_id": user.id})
        except Exception as e:
            current_app.logger.error("%s" % e)
            db.session.rollback()
            raise

    except Exception as e:
        current_app.logger.error("%s" % e)
        return api_abort(400)
        # raise


# 登录视图
@api_v1.route('/user/login', methods=["POST"])
def login():
    payload = request.json

    try:
        email = payload["username"]
        password = payload["password"]
        user = User.query.filter_by(email=email).first()

        if not bcrypt.checkpw(password.encode(), user.password.encode()):
            return api_abort(401, "用户名或密码错误")

        # 验证通过，生成token
        token = gen_token(user.id)
        response = {
            'code': 20000,
            'user': {
                'user_id': user.id,
                'username': user.username,
                'email': user.email
            },
            'token': token
        }
        current_app.logger.info("用户{}登录成功".format(user.username))
        return jsonify(response)
    except AttributeError as e:
        current_app.logger.error("{}".format(e))
        return api_abort(401, "用户名或密码错误")
    except Exception as e:
        current_app.logger.error("{}".format(e))
        return api_abort(401, "登录失败")


@api_v1.route('/user/logout', methods=['POST'])
@auth_required
def logout():
    r = redis.Redis(connection_pool=POOL)
    # 用户注销，将token加入到黑名单中
    r.zadd("token_blacklist", {g.token: int(datetime.datetime.now().timestamp())})
    return '', 204


@api_v1.route('/user/info', methods=['GET'])
@auth_required
def userinfo():
    return jsonify({
        "name": g.user.username,
        "avatar": url_for("api_v1.get_avatar", filename="dsb_s.png", _external=True)
    })


@api_v1.route('/user/check_user', methods=['POST'])
def check_user_exist():
    """检测用户是否已注册接口 1为已注册, 0为未注册"""
    ret = {"status": 0}
    username = request.json.get("username")
    if not username:
        return jsonify(ret)
    user = User.query.filter_by(username=username).first()
    if user:
        ret["status"] = 1
        return jsonify(ret)
    return jsonify(ret)


@api_v1.route('/user/check_email', methods=['POST'])
def check_email_exist():
    """检测邮箱否已注册接口"""
    ret = {"status": 0}
    email = request.json.get("email")
    if not email:
        return jsonify(ret)
    email = User.query.filter_by(email=email).first()
    if email:
        ret["status"] = 1
        return jsonify(ret)
    return jsonify(ret)


@api_v1.route('/test', methods=['GET'])
# @auth_required
def test():
    from sqlalchemy import func
    # print("=====" + repr(g.user))
    # query = User.query.filter(User.id == 1).one()
    # query = User.query.with_entities(func.count(User.id)).scalar()
    avatar = avatars.default()
    # print(query)
    return jsonify({"avatar": avatar})


@api_v1.route('/avatars/<path:filename>', methods=['GET'])
def get_avatar(filename):
    return send_from_directory(current_app.config['AVATARS_SAVE_PATH'], filename)
