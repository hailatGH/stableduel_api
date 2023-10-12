#!/bin/bash

E_BADARGS=65

if [ $# -eq 0 ]
then
  echo "Usage: `basename $0` {arg}"
  exit $E_BADARGS
fi

source /home/ubuntu/env/bin/activate
cd /home/ubuntu/stableduel/djangoapp
python manage.py $@
