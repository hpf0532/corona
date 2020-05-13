# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/5/13 上午11:59
# File: dingding.py
# IDE: PyCharm

import time
import hmac
import hashlib
import base64
import urllib.parse
from backend.settings import ROBOT_SECRET


def dingding_sign():
    """
    钉钉api签名
    :return:
    """
    timestamp = str(round(time.time() * 1000))
    secret = ROBOT_SECRET
    secret_enc = secret.encode('utf-8')
    string_to_sign = '{}\n{}'.format(timestamp, secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    return timestamp, sign


if __name__ == '__main__':
    ret = dingding_sign()
    print(ret)
