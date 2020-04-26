# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/4/26 上午10:21
# File: oss.py
# IDE: PyCharm
import oss2
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
                    max_age_seconds=1000)

    # 设置跨域规则
    bucket.put_bucket_cors(BucketCors([rule]))
