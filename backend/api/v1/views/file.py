# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/1 上午12:22
# File: file.py
# IDE: PyCharm
from datetime import datetime

from webargs import fields
from webargs.flaskparser import use_args
from flask import jsonify, request, g, current_app
from flask.views import MethodView
from sqlalchemy import text
from backend.api.v1 import api_v1
from backend.api.v1.schemas import files_schema, file_schema
from backend.decorators import auth_required
from backend.models import FileRepository
from backend.extensions import db
from backend.utils.utils import api_abort

# folder_args = 1
folder_args = {
    'name': fields.Str(validate=lambda p: len(p) > 0, required=True, error_messages=dict(
        required="文件夹为必填项", validator_failed="名称不能为空", invalid="请输入字符串"
    )),
    'folder_id': fields.Int(required=True)
}


@api_v1.route('/filerepo/check_folder', methods=['POST'])
@auth_required
def check_folder_exist():
    """检测文件夹是否已创建接口 1为已创建, 0为未创建"""
    ret = {"status": 0}
    name = request.json.get("name")
    folder_id = request.json.get("folder_id")
    print(request.json)
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


class FileListAPI(MethodView):
    decorators = [auth_required]
    parent_object = None

    def get(self):
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
        print(file_obj_list)
        # 计算导航条
        breadcrumb_list = []
        parent = self.parent_object
        while parent:
            breadcrumb_list.insert(0, {'id': parent.id, 'name': parent.name})
            parent = parent.parent
        print(breadcrumb_list)
        return jsonify(
            files_schema(file_obj_list, self.parent_object.id if self.parent_object else None, breadcrumb_list))


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
    def put(self, args, folder_id):
        folder_obj = FileRepository.query.get_or_404(folder_id)
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


@api_v1.route("/file", methods=["GET"])
def file():
    query = FileRepository.query.filter(
        FileRepository.user_id == 15,
        FileRepository.id == 1
    ).first()
    print(query.file_type.value)

    print(query.childs)

    return jsonify({"status": 200})


api_v1.add_url_rule('/filerepo/filelist', view_func=FileListAPI.as_view('files'), methods=['GET'])
api_v1.add_url_rule('/filerepo/folder', view_func=FolderAPI.as_view('folder_add'), methods=['POST'])
api_v1.add_url_rule('/filerepo/folder/<int:folder_id>', view_func=FolderAPI.as_view('folder_put'), methods=['PUT'])
