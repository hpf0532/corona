# from ansible_index import AnsibleOpt
# import datetime
# if __name__ == '__main__':
#     playbook_tid = "AnsibleApi-%s" % (datetime.datetime.now().strftime("%Y%m%d-%H%M%S"))
#     extra_vars = {'content': 'zhendiaosi'}
#     playbook = 'test_debug.yml'
#     hosts = ['192.168.1.1', 'tomcat', 'vm1']
#
#     # add.apply_async((1, 3))
#
#     AnsibleOpt.ansible_playbook(hosts, playbook, extra_vars=extra_vars)

# from sqlalchemy import func
# from backend.models import User
# from flask import Flask
# from flask_sqlalchemy import SQLAlchemy
# app = Flask(__name__)
# app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# db = SQLAlchemy(app)
# app.app_context().push()
#
# # query = User.query(func.count(User.id))
# query = User.query.filter(User.id==1).first()
#
# print(query)