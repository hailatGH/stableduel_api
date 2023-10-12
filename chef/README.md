# App Cookbook

This cookbook is designed for use in both a production and development environments.  It can be used locally leveraging the Berkshelf vagrant plugin and on AWS using an OpsWorks stack.

## Recipes

### system
This recipe installs all system-level dependencies.

### server
This recipe installs and configures `nginx`.  Specifically, it proxies <domain>/ to local port 8000.

### code
This recipe fetches the source of the application.  _It is intended to be run only on deploy targets._

### redis
This recipe ensures the systemd service `redis` is enabled and running.

### dev_database
This recipe simply installs PostgreSQL and creates a database with hardcoded credentials.  It is intended for development purposes only.

### django
This recipe assumes the django application source exists and installs any dependencies kept in version control. It configures the application based on environment variables.  Lastly, any database schema changes are applied.

### django\_daemon
This recipe ensures the systemd service `djangoapp` is enabled and running.

### celery
This recipe ensures the systemd service `celery` is enabled and running.

## License and Authors
Copyright (C) Stable Duel - All Rights Reserved

Unauthorized copying of this file, via any medium is strictly prohibited

Proprietary and confidential

Written by Matt Smith <matt@apaxsoftware.com>, April 2019