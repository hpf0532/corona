# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/4/6 下午10:47
# File: email.py
# IDE: PyCharm

from celery_tasks.tasks import send_mail


def send_confirm_email(user, token, domain, to=None):
    send_mail.delay(subject='Email Confirm', to=to or user.email, template='emails/confirm', user=user.username,
                    token=token, domain=domain)


def send_reset_password_email(user, token, domain):
    send_mail.delay(subject='Password Reset', to=user.email, template='emails/reset_password', user=user.username,
                    token=token,
                    domain=domain)


def send_change_email_email(user, token, to=None):
    send_mail(subject='Change Email Confirm', to=to or user.email, template='emails/change_email', user=user,
              token=token)
