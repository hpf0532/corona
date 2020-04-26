# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午4:35
# File: inventory.py
# IDE: PyCharm
import os

from webargs import fields
from sqlalchemy import text
from webargs.flaskparser import use_args, use_kwargs
from flask import request, jsonify, current_app, url_for
from flask.views import MethodView
from backend.api.v1 import api_v1
from backend.decorators import auth_required
from backend.models import HostGroup, Host, PlayBook, PlayBookDetail
from backend.api.v1.schemas import group_schema, groups_schema, host_schema, hosts_schema, playbook_schema, \
    playbooks_schema, play_detail_schema, host_group_schema
from backend.extensions import db
from backend.utils.utils import api_abort, validate_ip, validate_group_id, validate_playbook
from backend.settings import playbook_dir
from backend.utils.utils import model_to_dict

# 主机组参数校验
groups_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="主机组名为必填项", validator_failed="组名不能为空", invalid="请输入字符串"
    )),
    'description': fields.Str(missing='')
}

# 主机参数校验
hosts_args = {
    'hostname': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="主机名为必填项", validator_failed="组名不能为空", invalid="请输入字符串"
    )),
    'ip': fields.Str(validate=validate_ip, required=True, error_messages=dict(
        required="ip名为必填项", invalid="请输入字符串"
    )),
    'port': fields.Int(missing=22),
    'group_id': fields.Int(validate=validate_group_id, missing=None)
}

# playbook参数校验
playbooks_args = {
    'name': fields.Str(validate=validate_playbook, required=True, error_messages=dict(
        required="name为必填项", validator_failed="playbook不存在", invalid="请输入字符串"
    )),
    'author': fields.Str(validate=lambda p: len(p) > 0, required=True),
    'information': fields.Str(validate=lambda p: len(p) > 0, required=True),
    'is_env': fields.Boolean(missing=False)
}


class HostAPI(MethodView):
    decorators = [auth_required]

    def get(self, host_id):
        """获取单一主机接口"""
        host = Host.query.get_or_404(host_id)
        return jsonify(host_schema(host))

    @use_args(hosts_args, location='json')
    def put(self, args, host_id):
        """编辑主机接口"""
        host = Host.query.get_or_404(host_id)
        host.hostname = args['hostname']
        host.ip = args['ip']
        host.port = args['port']
        host.group_id = args['group_id']

        try:
            db.session.add(host)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "保存数据失败")
        return jsonify(host_schema(host))

    def delete(self, host_id):
        """删除主机接口"""
        host = Host.query.get_or_404(host_id)
        db.session.delete(host)
        db.session.commit()
        return '', 204


class HostsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """主机列表接口"""
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', type=int)
        name = request.args.get('name')
        group = request.args.get('group', type=int)
        sort = request.args.get('sort', '+id')
        per_page = limit or current_app.config['BACK_ITEM_PER_PAGE']
        pagination = Host.query.filter(
            # 查询搜索条件
            Host.hostname.like("%" + name + "%") if name else text(''),
            Host.group_id == group if group else text('')
        ).order_by(text(sort)).paginate(page, per_page)
        items = pagination.items
        current = url_for('.hosts', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.hosts', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.hosts', page=page + 1, _external=True)

        return jsonify(hosts_schema(items, current, prev, next, pagination))

    @use_args(hosts_args, location='json')
    def post(self, args):
        """新建主机接口"""
        host = Host(hostname=args["hostname"], ip=args['ip'], port=args['port'], group_id=args['group_id'])
        try:
            db.session.add(host)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(host_schema(host))
        response.status_code = 201
        return response


class GroupAPI(MethodView):
    decorators = [auth_required]

    def get(self, group_id):
        """获取单条组信息"""
        group = HostGroup.query.get_or_404(group_id)
        return jsonify(group_schema(group))

    @use_kwargs(groups_args, location="json")
    def put(self, group_id, name, description):
        """编辑主机组"""
        group = HostGroup.query.get_or_404(group_id)
        group.name = name
        group.description = description
        try:
            db.session.add(group)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(group_schema(group))

    def delete(self, group_id):
        """删除主机组接口"""
        group = HostGroup.query.get_or_404(group_id)
        db.session.delete(group)
        db.session.commit()
        return '', 204


class GroupsAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        """获取所有主机组接口"""
        groups = HostGroup.query.all()
        return jsonify(groups_schema(groups))

    @use_args(groups_args, location="json")
    def post(self, args):
        """
        创建新服务器组
        :param args:
        :return:
        """
        group = HostGroup(name=args['name'], description=args['description'])
        try:
            db.session.add(group)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(group_schema(group))
        response.status_code = 201
        return response


class PlaybookAPI(MethodView):
    decorators = [auth_required]

    def get(self, playbook_id):
        '''playbook详细获取接口'''
        playbook = PlayBook.query.get_or_404(playbook_id)
        return jsonify(play_detail_schema(playbook))

    @use_args(playbooks_args, location='json')
    def put(self, args, playbook_id):
        """编辑playbook接口"""
        playbook_file = os.path.join(playbook_dir, args['name'])
        # 读取playbook内容
        with open(playbook_file, encoding='utf8') as f:
            yml = f.read()

        playbook = PlayBook.query.get_or_404(playbook_id)
        playbook.name = args['name']
        playbook.author = args['author']
        playbook.information = args['information']
        playbook.is_env = args['is_env']
        playbook.detail.content = yml

        try:
            db.session.add(playbook)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(playbook_schema(playbook))

    def delete(self, playbook_id):
        """删除playbook接口"""
        playbook = PlayBook.query.get_or_404(playbook_id)
        db.session.delete(playbook)
        db.session.commit()
        return '', 204


class PlaybooksAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获取playbook接口"""
        playbooks = PlayBook.query.all()
        return jsonify(playbooks_schema(playbooks))

    @use_args(playbooks_args, location='json')
    def post(self, args):
        """创建playbook接口"""
        playbook_file = os.path.join(playbook_dir, args['name'])
        # 读取playbook内容
        with open(playbook_file, encoding='utf8') as f:
            yml = f.read()
        playbook = PlayBook(name=args['name'], author=args['author'], information=args['information'],
                            is_env=args['is_env'])
        try:
            db.session.add(playbook)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        play_content = PlayBookDetail()
        # commit提交后才能获取playbook的id
        play_content.playbook_id = playbook.id
        play_content.content = yml
        try:
            db.session.add(play_content)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")

        response = jsonify(playbook_schema(playbook))
        response.status_code = 201
        return response


class HostGroupSelectAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        data_list = []
        group_list = HostGroup.query.all()
        for group in group_list:
            data_list.append(
                {"group_id": group.id,
                 "group_name": group.name,
                 "hosts": host_group_schema(Host.query.filter(Host.group == group).all()),
                 }
            )
        default = Host.query.filter(Host.group == None).all()
        if default:
            data_list.append(
                {
                    "group_id": 0,
                    "group_name": "未分组",
                    "hosts": host_group_schema(default)
                }
            )
        return jsonify({
            "data": data_list
        })


# 添加路由
api_v1.add_url_rule('/hosts/<int:host_id>', view_func=HostAPI.as_view('host'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/hosts', view_func=HostsAPI.as_view('hosts'), methods=['GET', 'POST'])
api_v1.add_url_rule('/groups/<int:group_id>', view_func=GroupAPI.as_view('group'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/groups', view_func=GroupsAPI.as_view('groups'), methods=['GET', 'POST'])
api_v1.add_url_rule('/playbooks/<int:playbook_id>', view_func=PlaybookAPI.as_view('playbook'),
                    methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/playbooks', view_func=PlaybooksAPI.as_view('playbooks'), methods=['GET', 'POST'])
api_v1.add_url_rule('/group_hosts', view_func=HostGroupSelectAPI.as_view('host_groups'), methods=['GET'])
