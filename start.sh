#!/bin/bash

pkill -9 -f celery
supervisorctl stop corona-app

git pull
sleep 3

supervisorctl start corona-celery-beat
supervisorctl start corona-celery
supervisorctl start corona-app