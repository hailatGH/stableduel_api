from celery.task.schedules import crontab
from celery.decorators import periodic_task
from django.contrib.auth import get_user_model

from users.utils import set_global_leaderboard

User = get_user_model()

@periodic_task(
    run_every=(crontab(minute='*/30')),
    name="calculate_global_leaderboard",
    ignore_result=True
)
def calculate_global_leaderboard():
    set_global_leaderboard(User)