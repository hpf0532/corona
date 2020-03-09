# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/6 下午4:35
# File: inventory.py
# IDE: PyCharm

from webargs import fields
from webargs.flaskparser import use_args, use_kwargs
from flask import request, jsonify, current_app, url_for
from flask.views import MethodView
from backend.api.v1 import api_v1
from backend.models import HostGroup, Host
from backend.api.v1.schemas import group_schema, groups_schema, host_schema, hosts_schema
from backend.extensions import db
from backend.utils import api_abort, validate_ip, validate_group_id

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
        required="主机组名为必填项", validator_failed="组名不能为空", invalid="请输入字符串"
    )),
    'ip': fields.Str(validate=validate_ip, required=True, error_messages=dict(
        required="ip名为必填项", invalid="请输入字符串"
    )),
    'port': fields.Int(missing=22),
    'group_id': fields.Int(validate=validate_group_id, missing=None)
}


class HostAPI(MethodView):
    # decorators = [auth_required]

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
            api_abort(400, "保存数据失败")
        return jsonify(host_schema(host))

    def delete(self, host_id):
        """删除主机接口"""
        host = Host.query.get_or_404(host_id)
        db.session.delete(host)
        db.session.commit()
        return '', 204


class HostsAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        """主机列表接口"""
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['BACK_ITEM_PER_PAGE']
        pagination = Host.query.paginate(page, per_page)
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
    # decorators = [auth_required]

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

class PlaybooksAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        pass

    def post(self):
        pass


api_v1.add_url_rule('/hosts/<int:host_id>', view_func=HostAPI.as_view('host'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/hosts', view_func=HostsAPI.as_view('hosts'), methods=['GET', 'POST'])
api_v1.add_url_rule('/groups/<int:group_id>', view_func=GroupAPI.as_view('group'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/groups', view_func=GroupsAPI.as_view('groups'), methods=['GET', 'POST'])
api_v1.add_url_rule('/playbooks', view_func=PlaybooksAPI.as_view('playbook'), methods=['GET', 'POST'])

