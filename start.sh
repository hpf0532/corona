#!/bin/bash

pkill -9 -f celery
pkill -9 -f gunicorn

git pull
if [ $? -ne 0 ]; then
  echo "代码拉取失败，脚本退出"
  exit 2
fi
sleep 3

supervisorctl start corona-celery-beat
supervisorctl start corona-celery
supervisorctl start corona-app