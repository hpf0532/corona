# -*- coding: utf-8 -*-
# Author: hpf
# Date: 2020/3/1 上午10:44
# File: extensions.py
# IDE: PyCharm

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_avatars import Avatars

db = SQLAlchemy()
migrate = Migrate()
avatars = Avatars()
