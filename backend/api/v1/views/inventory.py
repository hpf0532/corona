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
from backend.models import HostGroup
from backend.api.v1.schemas import group_schema, groups_schema
from backend.extensions import db
from backend.utils import api_abort

groups_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, require=True, required=True, error_messages=dict(
        required="主机组名为必填项", validator_failed="组名不能为空", invalid="请输入字符串"
    )),
    'description': fields.Str(missing='')
}


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
        page = request.args.get('page', 1, type=int)
        per_page = current_app.config['BACK_ITEM_PER_PAGE']
        pagination = HostGroup.query.paginate(page, per_page)
        items = pagination.items
        current = url_for('api_v1.groups', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('api_v1.groups', page=page -1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('api_v1.groups', page=page + 1, _external=True)

        return jsonify(groups_schema(items, current, prev, next, pagination))

    @use_args(groups_args, location="json")
    def post(self, args):
        """
        创建新服务器组
        :param args:
        :return:
        """
        print(args)
        group = HostGroup(name=args['name'], description=args['description'])
        try:
            db.session.add(group)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        response = jsonify(group_schema(group))
        response.status_code = 201
        return response


api_v1.add_url_rule('/groups/<int:group_id>', view_func=GroupAPI.as_view('group'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/groups', view_func=GroupsAPI.as_view('groups'), methods=['GET', 'POST'])