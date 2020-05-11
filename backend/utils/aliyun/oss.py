# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/4/26 上午10:21
# File: oss.py
# IDE: PyCharm
import json

import oss2
from itertools import islice
from aliyunsdkcore import client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
from oss2.models import BucketCors, CorsRule
from flask import current_app


def create_bucket(bucket):
    """
    创建文件桶
    :param bucket: 桶名称
    :return:
    """
    auth = oss2.Auth(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, current_app.config['OSS_ENDPOINT'], bucket)
    bucketConfig = oss2.models.BucketCreateConfig(oss2.BUCKET_STORAGE_CLASS_STANDARD)
    bucket.create_bucket(oss2.BUCKET_ACL_PUBLIC_READ, bucketConfig)

    rule = CorsRule(allowed_origins=['*'],
                    allowed_methods=['GET', 'PUT', 'HEAD', 'POST', 'DELETE'],
                    allowed_headers=['*'],
                    expose_headers=['ETag'],
                    max_age_seconds=1000)

    # 设置跨域规则
    bucket.put_bucket_cors(BucketCors([rule]))


def delete_bucket(bucket):
    """
    刪除bucket
    1, 清空bucket下面所有文件
    2，清空bucket中的碎片文件
    3，刪除bucket
    :param bucket: 用戶bucket
    :return:
    """
    auth = oss2.Auth(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, current_app.config['OSS_ENDPOINT'], bucket)

    # 找到 & 刪除文件
    while True:
        part_obj = bucket.list_objects()
        if len(part_obj.object_list) == 0:
            break
        delete_list = [file.key for file in part_obj.object_list]

        # 批量刪除
        bucket.batch_delete_objects(delete_list)

        if not part_obj.is_truncated:
            break

    # 找到 & 刪除碎片文件
    while True:
        part_upload = bucket.list_multipart_uploads()
        if len(part_upload.upload_list) == 0:
            break
        for part in part_upload.upload_list:
            bucket.abort_multipart_upload(key=part.key, upload_id=part.upload_id)

        if not part_upload.is_truncated:
            break

    # 刪除桶
    bucket.delete_bucket()


def delete_file(bucket, key):
    """
    删除单个文件
    :param bucket: 桶名称
    :param key: 文件key
    :return:
    """
    auth = oss2.Auth(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, current_app.config['OSS_ENDPOINT'], bucket)
    bucket.delete_object(key)


def delete_file_list(bucket, key_list):
    """
    批量删除文件
    :param bucket:
    :param key_list:
    :return:
    """
    auth = oss2.Auth(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, current_app.config['OSS_ENDPOINT'], bucket)
    bucket.batch_delete_objects(key_list)


def check_file(bucket, key):
    """
    获取文件ETag值
    :param bucket: 桶
    :param key: 文件key
    :return:
    """
    auth = oss2.Auth(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'])
    bucket = oss2.Bucket(auth, current_app.config['OSS_ENDPOINT'], bucket)
    file_meta = bucket.get_object_meta(key)
    return file_meta


def get_sts_token():
    """
    获取sts临时token
    :return:
    """
    clt = client.AcsClient(current_app.config['ACCESS_KEY_ID'], current_app.config['ACCESS_KEY_SECRET'],
                           current_app.config['STS_REGION'])
    req = AssumeRoleRequest.AssumeRoleRequest()

    # 设置返回值格式为JSON。
    req.set_accept_format('json')
    req.set_RoleArn(current_app.config['ROLE_ARN'])
    req.set_RoleSessionName('session-name')
    req.set_DurationSeconds(900)
    body = clt.do_action_with_exception(req)

    # 使用RAM账号的AccessKeyId和AccessKeySecret向STS申请临时token。
    token = json.loads(body)
    return token
