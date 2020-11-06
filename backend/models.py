import sqlalchemy
from sqlalchemy_utils import ChoiceType
import sqlalchemy_utils
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


class User(db.Model):
    """用户表"""
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(48), unique=True, nullable=False)
    email = db.Column(db.String(64), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    bucket = db.Column(db.String(64), nullable=True, comment="用户桶名称")
    use_space = db.Column(db.Integer, default=0, comment="用户已使用空间")

    avatar_s = db.Column(db.String(64))
    avatar_m = db.Column(db.String(64))
    avatar_l = db.Column(db.String(64))

    # 邮箱确认字段
    confirmed = db.Column(db.Boolean, default=False)
    posts = db.relationship('Post', back_populates='author')

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


class Host(db.Model):
    """主机表"""
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


class HostGroup(db.Model):
    """主机组表"""
    __tablename__ = 'host_group'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False, unique=True)
    description = db.Column(db.String(128))
    # 关系定义,不会在数据库中生成字段
    hosts = db.relationship('Host', back_populates='group')

    def __repr__(self):
        return '<HostGroup %r>' % self.name


class PlayBook(db.Model):
    """playbook表"""
    __tablename__ = 'playbook'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(48), nullable=False, unique=True)
    author = db.Column(db.String(20), nullable=False)
    information = db.Column(db.String(48), nullable=False, unique=True)
    is_env = db.Column(db.Boolean, nullable=False, default=False)
    upload = db.Column(db.Boolean, nullable=False, default=False)
    step = db.Column(db.Integer, nullable=True)

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
    url = db.Column(db.String(128), nullable=True)

    playbook = db.relationship('PlayBook')
    env = db.relationship('Environment')

    def __repr__(self):
        return '<Options %r>' % self.name


class AnsibleTasks(db.Model):
    """ansible任务表"""
    __tablename__ = 'ansibletask'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    ansible_id = db.Column(db.String(80), unique=True, nullable=True)
    celery_id = db.Column(db.String(80), unique=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    group_name = db.Column(db.String(80), nullable=True)
    playbook = db.Column(db.String(80), unique=False, nullable=True)
    extra_vars = db.Column(db.Text, nullable=True)
    option_id = db.Column(db.Integer, db.ForeignKey('options.id', ondelete='SET NULL'), nullable=True)

    # True: 任务执行完成 False: 任务执行中
    status_choices = (
        (1, '执行中'),
        (2, '已完成'),
        (3, '任务失败'),
        (4, '任务取消')
    )
    state = db.Column(ChoiceType(status_choices, db.Integer()), nullable=False, default=0, comment="任务状态")
    # state = db.Column(db.Boolean, default=False, nullable=False)
    ansible_result = db.Column(db.Text(16777216))
    celery_result = db.Column(db.Text)
    create_time = db.Column(db.DateTime, default=datetime.datetime.now)
    cancelled = db.Column(db.Boolean, nullable=False, default=False)

    user = db.relationship('User')
    option = db.relationship('Options')
    # 排序
    __mapper_args__ = {
        "order_by": create_time.desc(),
    }

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.ansible_id)


class FileRepository(db.Model):
    """文件库"""
    __tablename__ = 'file_repository'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    file_type_choices = (
        (1, '文件'),
        (2, '文件夹')
    )
    file_type = db.Column(ChoiceType(file_type_choices, db.Integer()), nullable=True, comment="文件类型")
    name = db.Column(db.String(64), nullable=False, comment="文件/文件夹名称")
    key = db.Column(db.String(128), nullable=True, comment="文件存储在OSS中的KEY")
    file_size = db.Column(db.Integer, nullable=True, comment="文件大小/字节")
    file_path = db.Column(db.String(255), nullable=True, comment="文件路径")
    parent_id = db.Column(db.Integer, db.ForeignKey('file_repository.id'), nullable=True, comment="父级目录id")
    update_datetime = db.Column(db.DateTime, default=datetime.datetime.now, comment="更新时间")

    user = db.relationship('User')
    parent = db.relationship('FileRepository', remote_side=[id], back_populates='childs')
    childs = db.relationship('FileRepository', back_populates='parent', cascade='all')

    def __repr__(self):
        return "<{}: {}>".format(self.__class__.__name__, self.id)


class Category(db.Model):
    """wiki分类表"""
    __tablename__ = 'category'
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    name = db.Column(db.String(32), unique=True, comment="分类名称")
    posts = db.relationship('Post', back_populates='category')


class Post(db.Model):
    """wiki文章表"""
    id = db.Column(db.Integer, nullable=False, primary_key=True, autoincrement=True)
    title = db.Column(db.String(60), nullable=False, comment="文章标题")
    desc = db.Column(db.String(180), comment="文章摘要")
    body = db.Column(db.Text)
    published = db.Column(db.Boolean, nullable=False, default=False, comment="文档发布状态")
    create_time = db.Column(db.DateTime, default=datetime.datetime.now, comment="创建时间")
    update_time = db.Column(db.DateTime, default=datetime.datetime.now, comment="更新时间")
    # 与分类表关联
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    category = db.relationship('Category', back_populates='posts')
    # 作者
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    author = db.relationship('User', back_populates='posts')


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
