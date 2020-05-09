# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/8 下午4:22
# File: check_file_test.py
# IDE: PyCharm

import oss2

access_key_id = 'xxxxxxxxxxxxx'
access_key_secret = 'xxxxxxxxxxxxxxxxxxx'

auth = oss2.Auth(access_key_id, access_key_secret)
bucket = oss2.Bucket(auth, 'http://oss-cn-beijing.aliyuncs.com', 'haha1-1588759195')

simplifiedmeta = bucket.get_object_meta("1588926427000_Dashoard.html")

print(simplifiedmeta.etag)

from oss2.exceptions import NoSuchKey
