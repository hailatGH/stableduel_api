#!/home/ubuntu/env/bin python

from celery.task.control import inspect

i = inspect()

print(i.scheduled())
