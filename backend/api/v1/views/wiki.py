# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/19 上午11:31
# File: wiki.py
# IDE: PyCharm

from bs4 import BeautifulSoup
from webargs import fields
from flask import jsonify, current_app, request, g, url_for
from flask.views import MethodView
from webargs.flaskparser import use_args, use_kwargs

from backend.api.v1 import api_v1
from backend.extensions import db
from backend.models import Category, Post
from backend.api.v1.schemas import category_schema, categorys_schema, post_schema, posts_schema
from backend.decorators import auth_required
from backend.utils.utils import api_abort, validate_category_id

category_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0 and p != 'Default', required=True, error_messages=dict(
        required="分类名称为必填项", validator_failed="分类名不合法", invalid="请输入字符串"
    ))
}

post_args = {
    'title': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="标题为必填项", validator_failed="标题不能为空", invalid="请输入字符串"
    )),
    'body': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="正文必填项", validator_failed="内容不能为空", invalid="请输入字符串"
    )),
    'category_id': fields.Int(validate=validate_category_id, missing=1, default=1)
}


class CategoryAPI(MethodView):
    decorators = [auth_required]

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
    decorators = [auth_required]

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


class PostsAPI(MethodView):
    # decorators = [auth_required]

    def get(self):
        """
        分页获取文章列表
        :return:
        """
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', type=int)

        per_page = limit or current_app.config['BACK_ITEM_PER_PAGE']
        pagination = Post.query.paginate(page, per_page)
        items = pagination.items
        current = url_for('.options', page=page, _external=True)
        prev = None
        if pagination.has_prev:
            prev = url_for('.options', page=page - 1, _external=True)
        next = None
        if pagination.has_next:
            next = url_for('.options', page=page + 1, _external=True)
        return jsonify(posts_schema(items, current, prev, next, pagination))

    @use_args(post_args, location="json")
    def post(self, args):
        """
        新建文章
        :param args:
        :return:
        """
        content = args["body"]
        # 防止xss攻击,过滤script标签
        soup = BeautifulSoup(content, "html.parser")
        for tag in soup.find_all():
            if tag.name == "script":
                tag.decompose()
        # 构建摘要数据,获取标签字符串的文本前150个符号
        desc = soup.text[0:150] + "..."

        doc = Post()
        doc.title = args["title"]
        doc.category_id = args["category_id"]
        doc.desc = desc
        doc.body = str(soup)
        # doc.author = g.user
        doc.author_id = 20
        try:
            db.session.add(doc)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(post_schema(doc))
        response.status_code = 201
        return response


api_v1.add_url_rule('/category/<int:category_id>', view_func=CategoryAPI.as_view('category'),
                    methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/categorys', view_func=CategorysAPI.as_view('categorys'), methods=['GET', 'POST'])
api_v1.add_url_rule('/posts', view_func=PostsAPI.as_view('posts'), methods=['GET', 'POST'])
