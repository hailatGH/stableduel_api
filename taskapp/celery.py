
import os
import logging
from datetime import timedelta
import dotenv
from celery import Celery
from celery.task.schedules import crontab
from celery.utils.log import get_task_logger

from django.apps import apps, AppConfig
from django.conf import settings

logger = get_task_logger(__name__)
logger.level = logging.INFO


if not settings.configured:
    dotenv.read_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)+'/../'), '.env'))
    os.environ['DJANGO_DEBUG'] = 'False'

    # set the default Django settings module for the 'celery' program.
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')  # pragma: no cover

app = Celery('api')

class CeleryAppConfig(AppConfig):
    name = 'taskapp'
    verbose_name = 'Celery Config'

    def ready(self):
        # Using a string here means the worker will not have to
        # pickle the object when using Windows.
        # - namespace='CELERY' means all celery-related configuration keys
        #   should have a `CELERY_` prefix.
        app.config_from_object('django.conf:settings', namespace='CELERY')
        installed_apps = [app_config.name for app_config in apps.get_app_configs()]
        
        app.autodiscover_tasks(lambda: installed_apps, force=True)

@app.task(bind=True)
def debug_task(self):
    import time
    from django_celery_tracker.models import CeleryTask

    task = CeleryTask.objects.filter(task_id=self.request.id)

    logger.info('LEGEND')

    time.sleep(3)
    logger.info('wait for it...')
    task.update(progress=33)

    time.sleep(3)
    logger.info('wait for it...')
    task.update(progress=66)

    time.sleep(3)
    logger.info('DARY!')

    task.update(progress=100)
