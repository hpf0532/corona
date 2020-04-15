# Corona

Corona是基于ansible api开发的一款用于远程提交执行playbook的管理系统

## Components
- 语言: python3.6
- 后端框架: flask-1.1.1
- 任务执行框架: celery-4.4.1
- 前端框架: vue-2.9.6

## Installation

1. 配置python虚拟环境
```bash
$ virtualenv --python=/usr/bin/python3 corona
$ source corona/bin/activate
```

2. 安装supervisor
```bash
pip3 install git+https://github.com/Supervisor/supervisor#egg=supervisor
```

3. 下载源码
```bash
$ git clone https://github.com/hpf0532/corona.git
```

4. 安装依赖
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

5. 导入sql(mysql)
```bash
mysql -uroot -p < sql/ansible.sql

# mysql授权
> use mysql;
> grant all on ansible.* to 'ansible'@'%' identified by '123456';
> flush privileges;
```

6. 修改配置
```
backend/settings.py  .env  .flaskenv修改相关配置
```
.env文件配置样例
```
FLASK_APP='backend'
MYSQL_USER='ansible'
MYSQL_PASSWORD='123456'
MYSQL_HOST='127.0.0.1:3306'
SECRET_KEY="XXXXXXXXXXXXXXXXX"
MAIL_USERNAME='admin@admin.com'
MAIL_PASSWORD='123456'
MAIL_SERVER='smtp.admin.com'
REDIS_ADDR='127.0.0.1'
REDIS_PORT=6379
REDIS_PD='XXXXX'
```

## Usage

1. 运行flask app
```bash
$ gunicorn -w 4 -b 0.0.0.0:5000 wsgi:app
```

2. 运行celery beat任务
```bash
celery -A manage.celery beat
```

3. 运行celery worker进程
```bash
celery worker -A manage.celery -l info
```
可以配置使用supervisor作为进程管理工具

## License
[MIT](https://choosealicense.com/licenses/mit/)