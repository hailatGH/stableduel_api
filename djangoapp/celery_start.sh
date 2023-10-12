#!/bin/sh

echo "########### INITIALIZING CELERY ###########"
rm /tmp/celerybeat.pid
celery -A taskapp worker -c 4 --loglevel=INFO & \
celery -A taskapp beat -s /tmp/celerybeat-schedule --loglevel=INFO --pidfile /tmp/celerybeat.pid
