# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:44
# File: extensions.py
# IDE: PyCharm

import redis
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from flask_avatars import Avatars
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from backend.settings import POOL

db = SQLAlchemy()
migrate = Migrate()
mail = Mail()
avatars = Avatars()
limiter = Limiter(key_func=get_remote_address)

# redis连接
redis_conn = redis.Redis(connection_pool=POOL)
