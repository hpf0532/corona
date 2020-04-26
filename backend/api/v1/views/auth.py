# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/4 下午8:55
# File: auth.py
# IDE: PyCharm
import os
import uuid
import time
import redis
import base64
import datetime, bcrypt
from flask import jsonify, request, current_app, g
from webargs import fields, validate
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from sqlalchemy import or_
from webargs.flaskparser import use_args

from backend.utils.utils import api_abort, gen_token, validate_token, get_random_color, gen_captcha, validate_capcha, \
    isAlnum
from backend.utils.aliyun.oss import create_bucket
from backend.api.v1 import api_v1
from backend.models import User
from backend.decorators import auth_required
from backend.extensions import db, avatars, limiter
from backend.email import send_confirm_email, send_reset_password_email
from backend.settings import POOL, Operations, basedir

reset_password_args = {
    "email": fields.Email(required=True),
    "new_password": fields.Str(required=True, validate=validate.Length(min=6))
}


@api_v1.route("/capcha", methods=["GET"])
@limiter.limit("10/minute", error_message="获取验证码超频")
def get_capcha():
    height = 180
    width = 40

    # 生成image对象
    img_obj = Image.new(
        'RGB',
        (height, width),
        get_random_color()
    )
    # 在生成的图片上写字符
    # 生成一个图片画笔对象
    draw_obj = ImageDraw.Draw(img_obj)
    # 加载字体文件， 得到一个字体对象
    font_path = os.path.join(basedir, os.getenv("FLASK_APP"), "static/font/kumo.ttf")
    font_obj = ImageFont.truetype(font_path, 32)
    # 开始生成随机字符串并且写到图片上
    capcha, cap_list = gen_captcha()
    for i, letter in enumerate(cap_list):
        draw_obj.text((20 + 40 * i, 0), letter, fill=get_random_color(), font=font_obj)

    # 将图片保存至内存中
    io_obj = BytesIO()
    img_obj.save(io_obj, 'png')
    # print(io_obj.getvalue())

    img_base64 = "data:image/png;base64," + base64.b64encode(io_obj.getvalue()).decode()
    img_id = uuid.uuid4()
    r = redis.Redis(connection_pool=POOL)
    r.set(str(img_id), capcha.lower(), ex=60)

    # print(base64.b64decode(io_obj.getvalue()))
    # return jsonify({"data": data})
    return jsonify({"img_id": img_id, "img": img_base64})


# 注册视图
@api_v1.route("/user/reg", methods=["POST"])
def register():
    payload = request.json

    domain = request.headers.get('Origin')
    if not domain:
        return api_abort(403, "请使用浏览器登录")

    capcha = payload.get('capcha')
    capcha_id = payload.get('capcha_id')
    if not capcha or not capcha_id:
        return api_abort(400, "请输入验证码")
    if not validate_capcha(capcha_id, capcha):
        return api_abort(400, "验证码错误")

    try:  # 有任何异常，都返回400，如果保存数据出错，则向外抛出异常
        email = payload['email']
        username = payload['username']
        if not isAlnum(username):
            return api_abort(400, '用户名只能为字母和数字组合')

        user = User.query.filter(or_(User.username == username, User.email == email)).first()
        if user:
            return api_abort(400, "用户已注册")

        password = payload['password']
        bucket = '{}-{}'.format(username, str(int(time.time())))
        # 创建用户桶
        create_bucket(bucket)

        user = User(username=username, email=email)
        user.password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        user.bucket = bucket
        db.session.add(user)
        try:
            db.session.commit()
            token = gen_token(user=user, operation=Operations.CONFIRM, expire_in=3600)
            send_confirm_email(user=user, token=token, domain=domain)
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

    capcha = payload.get('capcha')
    capcha_id = payload.get('capcha_id')
    if not capcha or not capcha_id:
        return api_abort(400, "请输入验证码")
    if not validate_capcha(capcha_id, capcha):
        return api_abort(400, "验证码错误")

    try:
        email = payload["username"]
        password = payload["password"]
        user = User.query.filter_by(email=email).first()

        if not bcrypt.checkpw(password.encode(), user.password.encode()):
            return api_abort(401, "用户名或密码错误")

        # 验证通过，生成token
        token = gen_token(user, Operations.LOGIN)
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


@api_v1.route('/resend-confirm-email', methods=['GET'])
@limiter.limit("1/minute", error_message="验证邮件60秒只能发送一次")
@auth_required
def resend_confirm_email():
    """重新发送确认邮箱邮件"""
    try:
        domain = request.headers.get("Origin")
        if not domain:
            return api_abort(401, "请使用浏览器访问")
        if g.user.confirmed:
            return jsonify({"code": 20001, "message": "邮箱已认证"})
        token = gen_token(user=g.user, operation=Operations.CONFIRM, expire_in=3600)
        send_confirm_email(user=g.user, token=token, domain=domain)
        return jsonify({"code": 20005, "message": "验证邮件已发送"})
    except Exception as e:
        return api_abort(401, "数据有误")


@api_v1.route('/confirm/<token>', methods=['GET'])
@auth_required
def confirm(token):
    """邮箱验证"""
    domain = request.headers.get("Origin")
    if not domain:
        return api_abort(401, "请使用浏览器登录, 邮箱认证失败")
    if g.user.confirmed:
        return jsonify({"code": 20001, "message": "邮箱已认证"})
    if validate_token(user=g.user, token=token, operation=Operations.CONFIRM):
        return jsonify({"code": 20002, "message": "邮箱认证成功"})
    else:
        return jsonify({"code": 50001, "message": "邮箱认证失败"})


@api_v1.route('/forget-password', methods=['POST'])
def forget_password():
    """忘记密码接口"""
    try:
        domain = request.headers.get("Origin")
        if not domain:
            return api_abort(401, "请使用浏览器访问")

        capcha = request.json.get('capcha')
        capcha_id = request.json.get('capcha_id')
        if not capcha or not capcha_id:
            return api_abort(400, "请输入验证码")
        if not validate_capcha(capcha_id, capcha):
            return api_abort(400, "验证码错误")

        email = request.json["email"]
        user = User.query.filter_by(email=email).first()
        if not user:
            return api_abort(400, "邮箱错误")
        token = gen_token(user=user, operation=Operations.RESET_PASSWORD, expire_in=3600)
        send_reset_password_email(user=user, token=token, domain=domain)
        return jsonify({"code": 20003, "message": "重置密码邮件已发送"})
    except Exception as e:
        return api_abort(401, "数据有误")


@api_v1.route('/reset-password/<token>', methods=['POST'])
@use_args(reset_password_args, location="json")
def reset_password(args, token):
    """重置密码接口"""
    user = User.query.filter_by(email=args['email']).first()
    if not user:
        return api_abort(400, "邮箱错误")
    if validate_token(user=user, token=token, operation=Operations.RESET_PASSWORD, new_password=args['new_password']):
        return jsonify({"code": 20004, "message": "密码已更新, 请登录"})
    else:
        return jsonify({"code": 50002, "message": "token认证失败"})


@api_v1.route('/test', methods=['GET'])
# @auth_required
@limiter.limit("1/minute", error_message="验证邮件60秒只能发送一次")
def test():
    from sqlalchemy import func
    # print("=====" + repr(g.user))
    # query = User.query.filter(User.id == 1).one()
    # query = User.query.with_entities(func.count(User.id)).scalar()
    # avatar = avatars.default()
    # domain = request.headers.get('Origin')
    # user = User.query.filter(User.id == 2).one()
    # token = gen_token(user, Operations.CONFIRM)
    # send_confirm_email(user, token, domain)
    # print(request.headers.get('Origin'))

    # print(query)
    return jsonify({"avatar": 1})
