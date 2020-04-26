# Corona

Corona是基于ansible api开发的一款用于远程提交执行playbook的管理系统

## Components
- python版本: python3.6
- 后端框架: flask-1.1.1
- 任务执行框架: celery-4.4.1
- 前端框架: vue-2.9.6

## Installation
1. 安装python-devel  
由于阿里云OSS SDK需要crcmod库计算CRC校验码，而crcmod依赖Python.h文件，如果系统缺少这个头文件，安装SDK不会失败，但crcmod的C扩展模式安装会失败，因此导致上传、下载等操作效率非常低下。如果python-devel包不存在，则首先要安装这个包。
```bash
# 对于CentOS、RHEL、Fedora系统，请执行以下命令安装python-devel：
$ yum install -y python-devel
# 对于Debian，Ubuntu系统，请执行以下命令安装python-devel：
$ apt-get install python-dev
```

2. 配置python虚拟环境
```bash
$ virtualenv --python=/usr/bin/python3 corona
$ source corona/bin/activate
```

3. 安装supervisor
```bash
pip3 install git+https://github.com/Supervisor/supervisor#egg=supervisor
```

4. 下载源码
```bash
$ git clone https://github.com/hpf0532/corona.git
```

5. 安装依赖
```bash
pip3 install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

6. 导入sql(mysql)
```bash
mysql -uroot -p < sql/ansible.sql

# mysql授权
> use mysql;
> grant all on ansible.* to 'ansible'@'%' identified by '123456';
> flush privileges;
```

7. 修改配置
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