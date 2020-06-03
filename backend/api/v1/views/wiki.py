# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/19 上午11:31
# File: wiki.py
# IDE: PyCharm
import datetime

from sqlalchemy import text
from bs4 import BeautifulSoup
from webargs import fields
from flask import jsonify, current_app, request, g, url_for
from flask.views import MethodView
from webargs.flaskparser import use_args, use_kwargs

from backend.api.v1 import api_v1
from backend.extensions import db
from backend.models import Category, Post
from backend.api.v1.schemas import category_schema, categorys_schema, post_schema, posts_schema, post_detail_schema, \
    drafts_schema
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
    'category_id': fields.Int(validate=validate_category_id, allow_none=True, missing=1, default=1)
}


def filter_html(content):
    # 防止xss攻击,过滤script标签
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup.find_all():
        if tag.name == "script":
            tag.decompose()

    return soup


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
        # 删除分类后，将关联文章分类设置为default
        posts = category.posts
        print(posts)
        if posts:
            default = Category.query.get(1)
            default.posts.extend(posts)

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


class PostAPI(MethodView):
    decorators = [auth_required]

    def get(self, post_id):
        """
        文章详细接口
        :param post_id: 文章
        :return:
        """
        doc = Post.query.get_or_404(post_id)
        return jsonify(post_detail_schema(doc))

    @use_args(post_args, location="json")
    def put(self, args, post_id):
        """
        编辑文章接口
        :param args: 请求数据
        :param post_id: 文章ID
        :return:
        """
        doc = Post.query.get_or_404(post_id)
        # 作者本人才可编辑
        if g.user.id != doc.author.id:
            return api_abort(403, "您无法编辑此文章")
        content = args["body"]
        soup = filter_html(content)
        # 构建摘要数据,获取标签字符串的文本前150个符号
        desc = soup.text[0:150] + "..."

        doc.title = args["title"]
        doc.category_id = args["category_id"]
        doc.desc = desc
        doc.body = str(soup)
        doc.update_time = datetime.datetime.now()
        doc.author = g.user
        # doc.author_id = 20
        try:
            db.session.add(doc)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(post_schema(doc))

    def delete(self, post_id):
        """删除文章接口"""
        doc = Post.query.get_or_404(post_id)
        # 文章作者有删除权限
        if g.user.id != doc.author.id:
            return api_abort(403, "无法删除此文档")
        db.session.delete(doc)
        db.session.commit()
        return '', 204


class PostsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """
        分页获取文章列表
        :return:
        """
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', type=int)
        category_id = request.args.get('category_id', type=int)
        author_id = request.args.get('author_id', type=int)
        # 发布状态
        published = request.args.get('published', True)

        per_page = limit or current_app.config['BACK_ITEM_PER_PAGE']
        pagination = Post.query.filter(
            # 查询搜索条件
            Post.published == published,
            Post.category_id == category_id if category_id else text(''),
            Post.author_id == author_id if author_id else text('')
        ).order_by(text('-update_time')).paginate(page, per_page)
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
        soup = filter_html(content)
        # 构建摘要数据,获取标签字符串的文本前150个符号
        desc = soup.text[0:150] + "..."

        doc = Post()
        doc.title = args["title"]
        doc.category_id = args["category_id"] or 1
        doc.desc = desc
        doc.body = str(soup)
        doc.published = True
        doc.author = g.user
        # doc.author_id = 20
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


class DraftAPI(MethodView):
    decorators = [auth_required]

    def delete(self, draft_id):
        draft = Post.query.filter(Post.id == draft_id, Post.published == False).first()
        if not draft: return api_abort(404)
        # 文章作者有删除权限
        if g.user.id != draft.author.id:
            return api_abort(403, "无法删除此文档")
        db.session.delete(draft)
        db.session.commit()
        return '', 204


@api_v1.route('/delete-drafts', methods=['post'])
def batch_draft_del():
    pass


class DraftsAPI(MethodView):
    decorators = [auth_required]

    def get(self):
        """获取用户草稿列表接口"""
        drafts = Post.query.filter(Post.author == g.user, Post.published == False).order_by(text('-update_time')).all()
        return jsonify(drafts_schema(drafts))

    @use_args(post_args, location="json")
    def post(self, args):
        draft_id = request.args.get('draft_id', type=int)
        doc = Post.query.get(draft_id)
        if doc:
            if doc.published == True: return api_abort(403, "该文章已发布")
        else:
            doc = Post()
        content = args["body"]
        soup = filter_html(content)

        doc.title = args["title"]
        doc.body = str(soup)
        doc.update_time = datetime.datetime.now()
        doc.category_id = args["category_id"] or 1
        doc.author = g.user
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


# 路由规则
api_v1.add_url_rule('/category/<int:category_id>', view_func=CategoryAPI.as_view('category'),
                    methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/categorys', view_func=CategorysAPI.as_view('categorys'), methods=['GET', 'POST'])
api_v1.add_url_rule('/post/<int:post_id>', view_func=PostAPI.as_view('post'), methods=['GET', 'PUT', 'DELETE'])
api_v1.add_url_rule('/posts', view_func=PostsAPI.as_view('posts'), methods=['GET', 'POST'])
api_v1.add_url_rule('/drafts', view_func=DraftsAPI.as_view('drafts'), methods=['GET', 'POST'])
api_v1.add_url_rule('/draft/<int:draft_id>', view_func=DraftAPI.as_view('draft'), methods=['DELETE', ])
