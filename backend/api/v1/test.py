# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 下午12:15
# File: views.py
# Project: ansible_ui
# import datetime
# from flask import jsonify
# from backend.models import AnsibleTasks
# from backend.api.v1 import api_v1
# from ansible_index import AnsibleOpt
#
#
# @api_v1.route("/test", methods=["GET"])
# def hello():
#     # print(type(AnsibleTasks.query))
#     # print(result.ansible_id)
#     # print(r)
#     playbook_tid = "AnsibleApi-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
#     extra_vars = {'content': 'zhendiaosi'}
#     playbook = 'test_debug.yml'
#     hosts = ['192.168.1.1', 'tomcat', 'vm1']
#
#     AnsibleOpt.ansible_playbook(hosts, playbook, extra_vars=extra_vars)
#     return jsonify({"name": "test"})

import os
import time
import paramiko
from backend.settings import basedir

print(os.path.join(basedir, 'ssh_keys/id_rsa'))

key = paramiko.RSAKey.from_private_key_file(os.path.join(basedir, 'ssh_keys/id_rsa'))
ssh = paramiko.SSHClient()

ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

time1 = time.time()
from socket import timeout

# for x in range(10):
try:
    with paramiko.SSHClient() as ssh:
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect('alitest', username="root", pkey=key, timeout=5)
    # time.sleep(1)
    print(0)
except timeout as e:
    print(e)
    #     print(e)
    #     print(1)

time2 = time.time()

res = int(time2) - int(time1)
print(res)

# ssh.connect('alitest', username="root", pkey=key, timeout=10)
