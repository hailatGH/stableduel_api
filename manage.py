#!/usr/bin/env python
import os
import sys

import dotenv

from django.conf import settings

if __name__ == "__main__":

    dotenv_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    if os.path.isfile(dotenv_path):
        dotenv.read_dotenv(dotenv_path)

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

    try:
        from django.core.management import execute_from_command_line
    except ImportError:
        # The above import may fail for some other reason. Ensure that the
        # issue is really that Django is missing to avoid masking other
        # exceptions on Python 2.
        try:
            import django  # noqa
        except ImportError:
            raise ImportError(
                "Couldn't import Django. Are you sure it's installed and "
                "available on your PYTHONPATH environment variable? Did you "
                "forget to activate a virtual environment?"
            )

        raise

    # This allows easy placement of apps within the interior
    # api directory.
    current_path = os.path.dirname(os.path.abspath(__file__))

    execute_from_command_line(sys.argv)
