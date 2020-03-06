# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 下午12:15
# File: views.py
# Project: ansible_ui
import datetime
from flask import jsonify
from backend.models import AnsibleTasks
from backend.api.v1 import api_v1
from ansible_index import AnsibleOpt


@api_v1.route("/test", methods=["GET"])
def hello():
    print(type(AnsibleTasks.query))
    # print(result.ansible_id)
    # print(r)
    playbook_tid = "AnsibleApi-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
    extra_vars = {'content': 'zhendiaosi'}
    playbook = 'test_debug.yml'
    hosts = ['192.168.1.1', 'tomcat', 'vm1']

    AnsibleOpt.ansible_playbook(hosts, playbook, extra_vars=extra_vars)
    return jsonify({"name": "test"})