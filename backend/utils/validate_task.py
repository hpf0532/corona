# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/7/22 下午4:31
# File: validate_task.py
# IDE: PyCharm

import re


def task_verify(result):
    fail_pattern_ist = (
        re.compile(r'"status": "failed"'),
        re.compile(r'"status": "unreachable"')
    )

    for pattern in fail_pattern_ist:
        ret = pattern.search(result)

        if ret:
            return False
    return True
