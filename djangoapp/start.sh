#!/bin/sh
set -e

# if [ "$ENV" = "dev" ]
# then
#   echo "running migrations..."
#   python manage.py migrate --noinput
#   python manage.py runserver 0.0.0.0:8000

#   exec "$@"
# else
# /home/$USER/env/bin/gunicorn \
#   --name=djangoapp \
#   --bind=0.0.0.0:8000 \
#   --chdir /home/$USER/stableduel/djangoapp \
#   -k gevent \
#   -w 4 \
#   --max-requests 1000 \
#   --max-requests-jitter 30 \
#   config.wsgi:application
# fi

echo "#####running migrations..."
# python /home/stableduel/djangoapp/manage.py makemigrations
python /home/stableduel/djangoapp/manage.py migrate --noinput
python /home/stableduel/djangoapp/manage.py runserver 0.0.0.0:8000

exec "$@"
