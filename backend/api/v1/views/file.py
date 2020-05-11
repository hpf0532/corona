# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/1 上午12:22
# File: file.py
# IDE: PyCharm
import random
import time
import requests
from datetime import datetime
from urllib.parse import quote
from webargs import fields
from webargs.flaskparser import use_args
from flask import jsonify, request, g, current_app, Response, make_response
from flask.views import MethodView
from sqlalchemy import text
from backend.api.v1 import api_v1
from backend.api.v1.schemas import files_schema, file_schema
from backend.decorators import auth_required
from backend.models import FileRepository, User
from backend.extensions import db
from backend.utils.utils import api_abort
from backend.utils.aliyun.oss import delete_file, delete_file_list, get_sts_token, check_file, create_bucket

# folder_args = 1
folder_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="文件夹为必填项", validator_failed="名称不能为空", invalid="请输入字符串"
    )),
    'folder_id': fields.Int(required=True)
}

file_args = {
    'filename': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="文件名为必填项", validator_failed="文件名不能为空", invalid="请输入字符串"
    )),
    'file_size': fields.Int(required=True),
    'parent_id': fields.Int(required=True),
    'key': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="key为必填项", validator_failed="key不能为空", invalid="请输入字符串"
    )),
    'etag': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="etag为必填项", invalid="请输入字符串"
    )),
}


@api_v1.route('/filerepo/check_folder', methods=['POST'])
@auth_required
def check_folder_exist():
    """检测文件夹是否已创建接口 1为已创建, 0为未创建"""
    ret = {"status": 0}
    name = request.json.get("name")
    folder_id = request.json.get("folder_id")
    # print(request.json)
    if not name:
        return jsonify(ret)
    folder_obj = FileRepository.query.filter(
        FileRepository.user == g.user,
        FileRepository.parent_id == folder_id,
        FileRepository.name == name
    ).first()
    if folder_obj:
        ret["status"] = 1
        return jsonify(ret)
    return jsonify(ret)


@api_v1.route('/filerepo/add_bucket', methods=['GET'])
@auth_required
def add_bucket():
    """创建bucket接口"""
    if g.user.bucket:
        return api_abort(403, 'bucket已存在，不可重复创建')

    bucket = '{}-{}'.format(g.user.username, str(int(time.time())))
    # 创建用户桶
    create_bucket(bucket)
    g.user.bucket = bucket
    db.session.commit()
    return jsonify({'bucket': bucket})


class FileListAPI(MethodView):
    decorators = [auth_required]
    parent_object = None

    def get(self):
        bucket = g.user.bucket
        folder_id = request.args.get("folder", type=int)
        if folder_id:
            self.parent_object = FileRepository.query.filter_by(user=g.user, id=folder_id, file_type=2).first()
        # print(self.parent_object)
        queryset = FileRepository.query.filter_by(user=g.user)
        if self.parent_object:
            # 进入某目录
            file_obj_list = queryset.filter_by(parent=self.parent_object).order_by(text('-file_type')).all()
        else:
            # 根目录
            file_obj_list = queryset.filter_by(parent=None).order_by(text('-file_type')).all()
        # 计算导航条
        breadcrumb_list = []
        parent = self.parent_object
        while parent:
            breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent
        return jsonify(
            files_schema(file_obj_list, self.parent_object.id if self.parent_object else None, breadcrumb_list, bucket))


class FolderAPI(MethodView):
    decorators = [auth_required]

    @use_args(folder_args, location='json')
    def post(self, args):
        """新建文件夹"""
        folder = FileRepository(user=g.user, name=args['name'])
        folder.file_type = 2
        if args['folder_id']:
            folder.parent_id = args['folder_id']
        try:
            db.session.add(folder)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(e)
            return api_abort(400, "数据保存失败")
        response = jsonify(file_schema(folder))
        response.status_code = 201
        return response

    @use_args(folder_args, location='json')
    def put(self, args, fid):
        folder_obj = FileRepository.query.get_or_404(fid)
        folder_obj.name = args['name']
        folder_obj.update_datetime = datetime.now()
        try:
            db.session.add(folder_obj)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(file_schema(folder_obj))

    def delete(self, fid):
        # 删除数据库中的 文件 & 文件夹 （级联删除）
        del_obj = FileRepository.query.get_or_404(fid)
        if del_obj.file_type.code == 1:
            # 删除文件，将容量还给当前项目的已使用空间
            g.user.use_space -= del_obj.file_size
            if g.user.use_space < 0: g.user.use_space = 0

            # oss中删除文件
            delete_file(g.user.bucket, del_obj.key)

            # 在数据库中删除文件
            db.session.delete(del_obj)
            db.session.commit()
            return '', 204
        # 文件夹删除，需要找到文件夹下面的文件和文件夹，如果是文件，则归还容量并删除，如果是文件夹则继续循环
        total_size = 0
        key_list = []

        folder_list = [del_obj, ]
        for folder in folder_list:
            child_list = FileRepository.query.filter_by(user=g.user, parent=folder).order_by(text('-file_type')).all()
            # print(child_list)
            for child in child_list:
                if child.file_type == 2:
                    folder_list.append(child)
                else:
                    # 文件大小汇总
                    total_size += child.file_size
                    # 加入删除文件列表
                    key_list.append(child.key)

        # OSS批量删除文件
        if key_list:
            delete_file_list(g.user.bucket, key_list)

        # 归还用户已使用空间
        if total_size:
            g.user.use_space -= total_size
            if g.user.use_space < 0: g.user.use_space = 0

        db.session.delete(del_obj)
        db.session.commit()
        return '', 204


class FilePostAPI(MethodView):
    """文件上传后保存至数据库中"""
    decorators = [auth_required]

    @use_args(file_args, location='json')
    def post(self, args):

        key = args['key']
        etag = args['etag']

        # 向OSS校验etag值
        from oss2.exceptions import NoSuchKey
        try:
            res = check_file(g.user.bucket, key)
            if etag != res.etag:
                return api_abort(403, "ETag错误")
        except NoSuchKey as e:
            return api_abort(403, "文件未上传成功")

        # user = User.query.filter_by(id=g.user.id).with_for_update(read=False).first()

        file_obj = FileRepository(name=args["filename"])
        file_path = "http://{}.{}.aliyuncs.com/{}".format(g.user.bucket, current_app.config['OSS_REGION'], args['key'])
        file_obj.user = g.user
        file_obj.file_type = 1
        file_obj.file_size = args['file_size']
        file_obj.parent_id = args['parent_id'] if args['parent_id'] else None
        file_obj.key = key
        file_obj.file_path = file_path

        g.user.use_space += args['file_size']
        db.session.commit()

        # print(g.user.use_space)

        try:
            db.session.add(file_obj)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(e)
            db.session.rollback()
            return api_abort(400, "数据保存失败")
        return jsonify(file_schema(file_obj))


class StsTokenAPI(MethodView):
    """获取OSS临时token"""
    decorators = [auth_required]

    def post(self):
        filename = request.json.get("name")
        filesize = request.json.get("size")
        if not filename or not filesize:
            return api_abort(400, "请选择文件")

        if filesize > 5 * 1024 * 1024:
            return api_abort(403, '单文件不能超过5M')

        if filesize + g.user.use_space > 100 * 1024 * 1024:
            return api_abort(403, '您的容量已不足，请升级套餐')
        # print(filename, filesize)
        token = get_sts_token()
        # print(token)
        token['region'] = current_app.config['OSS_REGION']
        token['bucket'] = g.user.bucket

        return jsonify(token)


class FileDownloadAPI(MethodView):
    """下载文件"""

    # decorators = [auth_required]

    def get(self, file_id):
        file_obj = FileRepository.query.get_or_404(file_id)

        res = requests.get(file_obj.file_path)

        # 文件分块处理，适用于大文件
        data = res.iter_content()

        response = make_response(Response(data))
        # 设置响应头，用于提示下载框
        response.headers['content_type'] = "application/octet-stream"
        # 设置用户名，增加中文转义
        response.headers['Content-Disposition'] = "attachment; filename={};".format(quote(file_obj.name, 'utf-8'))

        return response


@api_v1.route("/file", methods=["GET"])
def file():
    # query = FileRepository.query.filter(
    #     FileRepository.user_id == 15,
    #     FileRepository.id == 1
    # ).first()
    import oss2
    from backend.utils.aliyun.oss import delete_bucket
    try:
        delete_bucket("hepengfei-159086320")
    except oss2.exceptions.NoSuchBucket:
        return api_abort(404, "找不到指定的桶")

    # for b in part:
    #     print(b.key)

    # print(query.file_type.value)

    # print(query.childs)

    return jsonify({"status": 200})


api_v1.add_url_rule('/filerepo/filelist', view_func=FileListAPI.as_view('files'), methods=['GET'])
api_v1.add_url_rule('/filerepo/folder', view_func=FolderAPI.as_view('folder_add'), methods=['POST'])
api_v1.add_url_rule('/filerepo/folder/<int:fid>', view_func=FolderAPI.as_view('folder_put_delete'),
                    methods=['PUT', 'DELETE'])
api_v1.add_url_rule('/filerepo/sts_token', view_func=StsTokenAPI.as_view('sts_token'), methods=['POST'])
api_v1.add_url_rule('/filerepo/file_post', view_func=FilePostAPI.as_view('file_post'), methods=['POST'])
api_v1.add_url_rule('/filerepo/download/<int:file_id>', view_func=FileDownloadAPI.as_view('file_download'),
                    methods=['GET'])
