#!/bin/bash

export PGPASSWORD=password
export DATABASE_URL=postgres://postgres:password@localhost:5432/testdb
export CELERY_TASK_ALWAYS_EAGER=true
export WINDOWS_MNT_PATH=/home/vagrant/stableduel/djangoapp/api/tests/sample_output
export DJANGO_MEDIA_ROOT=/home/vagrant/tmp-media

mkdir $DJANGO_MEDIA_ROOT

# Create blank DB
psql -h 127.0.0.1 -U postgres -c 'DROP DATABASE IF EXISTS testdb' > /dev/null 2>&1
psql -h 127.0.0.1 -U postgres -c 'CREATE DATABASE testdb' > /dev/null
/home/vagrant/env/bin/python manage.py migrate  > /dev/null

# Create test data
/home/vagrant/env/bin/python manage.py create_test_data

/home/vagrant/env/bin/python manage.py dumpdata > api/codes/fixtures/test_codes.json

rm -rf $DJANGO_MEDIA_ROOT