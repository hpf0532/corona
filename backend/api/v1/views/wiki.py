# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/19 上午11:31
# File: wiki.py
# IDE: PyCharm

from webargs import fields
from flask import jsonify, current_app
from flask.views import MethodView
from webargs.flaskparser import use_args, use_kwargs

from backend.api.v1 import api_v1
from backend.extensions import db
from backend.models import Category
from backend.api.v1.schemas import category_schema, categorys_schema
from backend.decorators import auth_required
from backend.utils.utils import api_abort

category_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="分类名称为必填项", validator_failed="分类名不能为空", invalid="请输入字符串"
    ))
}


class CategoryAPI(MethodView):
    # decorators = [auth_required]

    def get(self, category_id):
        """获取单条分类信息"""
        category = Category.query.get_or_404(category_id)
        return jsonify(category_schema(category))

    @use_kwargs(category_args, location="json")
    def put(self, category_id, name):
        """编辑分类"""
        category = Category.query.get_or_404(category_id)
        category.name = name
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(category_schema(category))

    def delete(self, category_id):
        """删除分类接口"""
        category = Category.query.get_or_404(category_id)
        db.session.delete(category)
        db.session.commit()
        return '', 204


class CategorysAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        """获取所有分类接口"""
        categorys = Category.query.all()
        return jsonify(categorys_schema(categorys))

    @use_args(category_args, location="json")
    def post(self, args):
        """
        创建新分类
        :param args:
        :return:
        """
        category = Category(name=args['name'])
        try:
            db.session.add(category)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(category_schema(category))
        response.status_code = 201
        return response


api_v1.add_url_rule('/category/<int:category_id>', view_func=CategoryAPI.as_view('category'),
                    methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/categorys', view_func=CategorysAPI.as_view('categorys'), methods=['GET', 'POST'])
