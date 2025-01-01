from datetime import date
from django.contrib.auth import get_user_model
from django_redis import get_redis_connection
from django.db.models import Case, When, Sum, Value as V
from django.db.models.functions import Coalesce
from django.core.cache import cache
from datetime import datetime

def format_score(score):
    new_score = Decimal(Decimal(score).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
    return int(new_score) if new_score % 1 == 0 else new_score

def get_rank(total_score):
    """
    Gets the rank for a score
    """
    conn = get_redis_connection('default')
    rank = conn.zcount('global_leaderboard','({}'.format(float(total_score)), '+inf')
    return rank + 1 if rank is not None else None

def get_user_rank(user):
    cache_key = 'stable_points_{}'.format(user.id)
    
    current_score_rank = cache.get(cache_key)
    return  current_score_rank if current_score_rank is not None else (0, None, )

def set_global_leaderboard(User):
    conn = get_redis_connection('default')
    
    users = User.objects.all().annotate(stable_points_sum=Coalesce(Sum(Case(When(stablepoint__created_at__year=datetime.now().year, then='stablepoint__points'))), V(0)))

    conn.zadd('global_leaderboard', {"{}".format(user.id): float(user.stable_points_sum) for user in users})

    stable_points_set = {
        'stable_points_{}'.format(user.id): (user.stable_points_sum, get_rank(user.stable_points_sum), ) 
            for user in users
    }

    cache.set_many(
        stable_points_set,
        None
    )

def get_user_ids(top, bottom):
    conn = get_redis_connection('default')
    ids = conn.zrevrange('global_leaderboard', bottom, top-1)

    return [int(id) for id in ids]

def get_user_count():
    conn = get_redis_connection('default')
    count = conn.zcount('global_leaderboard','-inf', '+inf')

    return count

def get_custom_user_properties(user):
    user_properties = ""
    user_properties = {
        'rank': get_user_rank(user),
        'stable_points': user.stable_points_sum,
        'contests_entered': "",
        'stables_entered': "",
        'followed_horses': "",
        'followed_stables': "",
        'win_count': "",
        'races_run': "",
        'place_count': "",
        'show_count': "",
        'fourth_count': "",
        'fifth_count': "",
     }

    return user_properties