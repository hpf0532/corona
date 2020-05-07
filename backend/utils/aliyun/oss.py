# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/4/26 上午10:21
# File: oss.py
# IDE: PyCharm
import json

import oss2
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
