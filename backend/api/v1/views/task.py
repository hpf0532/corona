# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/10 下午4:01
# File: task.py
# IDE: PyCharm
import json, os
from datetime import datetime
from sqlalchemy import text
from webargs import fields
from webargs.flaskparser import use_args
from flask import request, jsonify, current_app, url_for
from flask.views import MethodView
from backend.api.v1 import api_v1
from backend.extensions import db
from backend.models import Host, PlayBook, AnsibleTasks, Options, Environment
from backend.utils.utils import api_abort, validate_env_id, validate_playbook_id, validate_json
from backend.decorators import auth_required, confirm_required
from backend.api.v1.schemas import tasks_schema, task_detail_schema, flush_task_schema, option_schema, options_schema, \
    envs_schema, task_options_schema
from ansible_index import AnsibleOpt

# 校验option参数
options_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="option名称为必填项", validator_failed="name不能为空", invalid="请输入字符串"
    )),
    'playbook_id': fields.Int(validate=validate_playbook_id, required=True, error_messages=dict(
        required="playbook必填项"
    )),
    'content': fields.Dict(required=True),
    'env_id': fields.Int(required=False, validate=validate_env_id, allow_none=True, missing=None, default=None),
    'url': fields.Url(required=False, allow_none=True, missing=None, default=None)
}


class PlayBookOptionAPI(MethodView):
    decorators = [auth_required]

    def get(self, option_id):
        """获取单一playbook参数接口"""
        option = Options.query.get_or_404(option_id)
        return jsonify(option_schema(option))

    @use_args(options_args, location='json')
    def put(self, args, option_id):
        """编辑playbook参数接口"""
        option = Options.query.get_or_404(option_id)
        option.name = args['name']
        option.content = json.dumps(args['content'])
        option.playbook_id = args['playbook_id']
        option.env_id = args.get('env_id')
        option.url = args.get('url')


        try:
            db.session.add(option)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "保存数据失败")
        return jsonify(option_schema(option))

    def delete(self, option_id):
        """删除playbook参数接口"""
        option = Options.query.get_or_404(option_id)
        db.session.delete(option)
        db.session.commit()
        return '', 204


class PlayBookOptionsAPI(MethodView):
    """playbook参数列表接口"""
    decorators = [auth_required]

    def get(self):
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', type=int)
        name = request.args.get('name')
        playbook = request.args.get('playbook', type=int)
        env = request.args.get('env', type=int)
        sort = request.args.get('sort', '+id')
        per_page = limit or current_app.config['BACK_ITEM_PER_PAGE']
        pagination = Options.query.filter(
            # 查询搜索条件
            Options.name.like("%" + name + "%") if name else text(''),
            Options.playbook_id == playbook if playbook else text(''),
            Options.env_id == env if env else text('')
        ).order_by(text(sort)).paginate(page, per_page)
        items = pagination.items
        current = url_for('.options', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.options', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.options', page=page + 1, _external=True)

        return jsonify(options_schema(items, current, prev, next, pagination))

    @use_args(options_args, location='json')
    def post(self, args):
        """新建playbook任务参数"""
        option = Options()
        option.name = args['name']
        option.content = json.dumps(args['content'])
        option.playbook_id = args['playbook_id']
        option.env_id = args.get('env_id')
        option.url = args.get('url')

        print(type(option.content), option.content)
        try:
            db.session.add(option)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print(e)
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(option_schema(option))
        response.status_code = 201
        return response


class TaskOptionsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """任务参数接口"""
        playbook = request.args.get('playbook', type=int)
        env = request.args.get('env', type=int)
        options = Options.query.filter(
            Options.playbook_id == playbook if playbook else text(''),
            Options.env_id == env if env else text('')
        ).all()

        return jsonify(task_options_schema(options))


class TaskAPI(MethodView):
    decorators = [auth_required]

    def get(self, task_id):
        """获取任务详细信息接口"""
        task = AnsibleTasks.query.get_or_404(task_id)
        return jsonify(task_detail_schema(task))


class TasksAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """分页获取task任务列表"""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', type=int)
        start = request.args.get('startTime', type=int)
        end = request.args.get('endTime', type=int)
        user = request.args.get('user')
        ansible_id = request.args.get('ansibleId')

        per_page = limit or current_app.config['BACK_ITEM_PER_PAGE']
        pagination = AnsibleTasks.query.filter(
            # 根据ansible_id查询任务
            AnsibleTasks.ansible_id.like("%" + ansible_id + "%") if ansible_id else text(''),
            # 根据时间区间查询相应的任务
            AnsibleTasks.create_time > datetime.fromtimestamp(start) if start else text(''),
            AnsibleTasks.create_time < datetime.fromtimestamp(end) if end else text(''),
            AnsibleTasks.user_id == user if user else text('')
        ).paginate(page, per_page)
        items = pagination.items
        current = url_for('.tasks', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.tasks', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.tasks', page=page + 1, _external=True)

        return jsonify(tasks_schema(items, current, prev, next, pagination))

    @confirm_required
    def post(self):
        """提交任务接口"""
        print(request.json)
        exec_hosts = []
        payload = request.json
        try:
            host = payload["hosts"]
            playbook = payload["playbook"]
            extra_vars = payload["extra_vars"]
            option = payload['option']
            if not option: option = None
            if not host or not playbook:
                return api_abort(400, "参数有误")
        except Exception as e:
            return api_abort(400, "参数有误")
        hosts = Host.query.filter(Host.id.in_(host)).all()
        print(hosts)
        if not hosts:
            return api_abort(400, "参数有误")
        for host in hosts:
            exec_hosts.append((host.ip, host.port))

        playbook = PlayBook.query.get_or_404(playbook)
        playbook = playbook.name

        ret = AnsibleOpt.ansible_playbook(exec_hosts, playbook, option, extra_vars=extra_vars)

        return jsonify(ret)


class FlushTaskAPI(MethodView):
    decorators = [auth_required]

    def get(self, task_id):
        """轮询task结果接口"""
        task = AnsibleTasks.query.get_or_404(task_id)
        return jsonify(flush_task_schema(task))


class EnvsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获取所有环境信息接口"""
        envs = Environment.query.all()
        return jsonify(envs_schema(envs))


class UploadDistAPI(MethodView):
    decorators = [auth_required]

    def post(self):
        """上传dist压缩文件接口"""
        data = {"code": 2000, "msg": ''}
        try:
            project = request.args.get('option')
            file_obj = request.files["files"]
            if not project:
                return api_abort(403, "请先选择参数")
            if not file_obj or file_obj.filename.split(".")[-1] != "zip":
                return api_abort(403, "请上传zip文件")

            upload_path = os.path.join(current_app.config["UPLOAD_PATH"], project)
            # 如果目录不存在，则创建
            if not os.path.exists(upload_path):
                os.mkdir(upload_path)

            file_obj.save(os.path.join(upload_path, "dist.zip"))
        except Exception as e:
            data["code"] = 5001
            data["msg"] = "文件上传失败"

        return jsonify(data)


# 添加路由
api_v1.add_url_rule('/envs', view_func=EnvsAPI.as_view('envs'), methods=['GET'])
api_v1.add_url_rule('/options', view_func=PlayBookOptionsAPI.as_view('options'), methods=['GET', 'POST'])
api_v1.add_url_rule('/options/<int:option_id>', view_func=PlayBookOptionAPI.as_view('option'),
                    methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/tasks', view_func=TasksAPI.as_view('tasks'), methods=['GET', 'POST'])
api_v1.add_url_rule('/tasks/<int:task_id>', view_func=TaskAPI.as_view('task'), methods=['GET'])
api_v1.add_url_rule('/flush_task/<int:task_id>', view_func=FlushTaskAPI.as_view('flush_task'), methods=['GET'])
api_v1.add_url_rule('/task_options', view_func=TaskOptionsAPI.as_view('task_options'), methods=['GET'])
api_v1.add_url_rule('/upload_dist', view_func=UploadDistAPI.as_view('upload_dist'), methods=['POST'])
