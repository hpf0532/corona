# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/6 下午4:20
# File: aliyun_sts_test.py
# IDE: PyCharm


from aliyunsdkcore import client
from aliyunsdksts.request.v20150401 import AssumeRoleRequest
import json
import oss2

access_key_id = 'xxxxxxxxxxxx'
access_key_secret = 'xxxxxxxxxxxxxxxx'
role_arn = 'xxxxxxxxxxxxxxxs'

clt = client.AcsClient(access_key_id, access_key_secret, 'cn-beijing')
req = AssumeRoleRequest.AssumeRoleRequest()

# 设置返回值格式为JSON。
req.set_accept_format('json')
req.set_RoleArn(role_arn)
req.set_RoleSessionName('session-name')
req.set_DurationSeconds(1800)
body = clt.do_action_with_exception(req)

# 使用RAM账号的AccessKeyId和AccessKeySecret向STS申请临时token。
token = json.loads(body)
print(token)
