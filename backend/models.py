import sqlalchemy
import json
import datetime
# from sqlalchemy import create_engine, Column, DateTime, Integer, String, Text
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import sessionmaker
from backend.extensions import db
from flask_avatars import Identicon

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
    bucket = db.Column(db.String(64), nullable=True, comment="用户桶名称")

    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))

    # 邮箱确认字段
    confirmed = db.Column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.generate_avatar()

    def generate_avatar(self):
        avatar = Identicon()
        filenames = avatar.generate(text=self.username)
        self.avatar_s = filenames[0]
        self.avatar_m = filenames[1]
        self.avatar_l = filenames[2]
        db.session.commit()

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

    def __repr__(self):
        return '<Host %r>' % self.hostname


# 主机组表
class HostGroup(db.Model):
    __tablename__ = 'host_group'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False, unique=True)
    description = db.Column(db.String(128))
    # 关系定义,不会在数据库中生成字段
    hosts = db.relationship('Host', back_populates='group')

    def __repr__(self):
        return '<HostGroup %r>' % self.name


class PlayBook(db.Model):
    __tablename__ = 'playbook'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False, unique=True)
    author = db.Column(db.String(20), nullable=False)
    information = db.Column(db.String(48), nullable=False, unique=True)
    is_env = db.Column(db.Boolean, nullable=False, default=False)
    # 建立一对一关系
    detail = db.relationship('PlayBookDetail', back_populates='playbook', uselist=False, cascade='all')

    def __repr__(self):
        return '<PlayBook %r>' % self.name


class PlayBookDetail(db.Model):
    __tablename__ = 'playbook_detail'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    playbook_id = db.Column(db.Integer, db.ForeignKey('playbook.id'), nullable=False)
    content = db.Column(db.Text)
    playbook = db.relationship('PlayBook', back_populates='detail')

    def __repr__(self):
        return '<PlayBookDetail %r>' % self.id


class Environment(db.Model):
    """环境信息"""
    __tablename__ = 'environment'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return '<Environment %r>' % self.name


class Options(db.Model):
    """playbook选项参数"""
    __tablename__ = 'options'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False)
    content = db.Column(db.Text, nullable=True)
    playbook_id = db.Column(db.Integer, db.ForeignKey('playbook.id'), nullable=False)
    env_id = db.Column(db.Integer, db.ForeignKey('environment.id'))

    playbook = db.relationship('PlayBook')
    env = db.relationship('Environment')

    def __repr__(self):
        return '<Options %r>' % self.name


# 创建ansible任务表
class AnsibleTasks(db.Model):
    __tablename__ = 'ansibletask'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    ansible_id = db.Column(db.String(80), unique=True, nullable=True)
    celery_id = db.Column(db.String(80), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group_name = db.Column(db.String(80), nullable=True)
    playbook = db.Column(db.String(80), unique=False, nullable=True)
    extra_vars = db.Column(db.Text, nullable=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id'), nullable=True)

    # True: 任务执行完成 False: 任务执行中
    state = db.Column(db.Boolean, default=False, nullable=False)
    ansible_result = db.Column(db.Text(16777216))
    celery_result = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)

    user = db.relationship('User')
    option = db.relationship('Options')
    # 排序
    __mapper_args__ = {
        "order_by": create_time.desc(),
    }

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
