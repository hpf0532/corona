import sqlalchemy
import json
import datetime
# from sqlalchemy import create_engine, Column, DateTime, Integer, String, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
from backend.extensions import db

# connstr = "{}://{}:{}@{}:{}/{}".format(
#     "mysql+pymysql", "ansible", "qingdao@123QWE",
#     "127.0.0.1", 3306, "ansible"
# )

# engine = create_engine(connstr, echo=True)
#
# Base = declarative_base()


# 用户表
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(48), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return '<User %r>' % self.username


# 主机表
class Host(db.Model):
    __tablename__ = 'host'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    hostname = db.Column(db.String(60), nullable=False, unique=True)
    ip = db.Column(db.String(20), nullable=False, unique=True)
    port = db.Column(db.Integer, nullable=False, default=22)
    group_id = db.Column(db.Integer, db.ForeignKey('host_group.id'), nullable=True)
    # 关系标量
    group = db.relationship('HostGroup', back_populates='hosts')


# 主机组表
class HostGroup(db.Model):
    __tablename__ = 'host_group'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False, unique=True)
    description = db.Column(db.String(128))
    # 关系定义,不会在数据库中生成字段
    hosts = db.relationship('Host', back_populates='group')


# 创建ansible任务表
class AnsibleTasks(db.Model):
    __tablename__ = 'ansibletask'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    ansible_id = db.Column(db.String(80), unique=True, nullable=True)
    celery_id = db.Column(db.String(80), unique=True, nullable=True)
    group_name = db.Column(db.String(80), nullable=True)
    playbook = db.Column(db.String(80), unique=False, nullable=True)
    extra_vars = db.Column(db.Text, nullable=True)
    ansible_result = db.Column(db.Text)
    celery_result = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.ansible_id)

# 删除继承自Base的所有表
# Base.metadata.drop_all(engine)
# 创建继承自Base的所有表
# Base.metadata.create_all(engine)

# 创建session
# Session = sessionmaker(bind=engine)
# session = Session()


if __name__ == '__main__':

    extra_vars = {"content": "name"}
    print("========", json.dumps(extra_vars), type(json.dumps(extra_vars)))
    at = AnsibleTasks(
        ansible_id="test_ansible_task1",
        celery_id="celery_task_id1",
        extra_vars=json.dumps(extra_vars),
        playbook="test_debug.yml",
    )
    db.session.add(at)
    db.session.commit()
