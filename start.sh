#!/bin/bash

pkill -9 -f celery
pkill -9 -f gunicorn

git pull
sleep 3

supervisorctl start corona-celery-beat
supervisorctl start corona-celery
supervisorctl start corona-app