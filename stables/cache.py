from django.core.cache import cache
from django_redis import get_redis_connection
from stables.models import Runner
def get_stable_score(stable, runner_scores):
    runners = stable.runners.all()
    total_score = sum([runner_scores[runner.id] for runner in runners])
    return (stable, total_score, )

def get_rank(game, total_score):
    conn = get_redis_connection('default')
    rank = conn.zrevrank('stable_ranks_{}'.format(game.id)) + 1
    return rank

def calculate_scores(game):
    conn = get_redis_connection('default')

    runners = Runner.objects.filter(racecard=game.racecard)
    runners_scores = {runner.id: runner.score for runner in runners}

    stables = Stable.objects.filter(game=game).prefetch_related('runners')

    stable_scores = [get_stable_score(stable, runner_scores) for stable in stables]
    conn.zadd('stable_ranks_{}'.format(game.id), **{str(total_score): total_score})
    
    cache.set_many(
        { 'stable_scores_{}_{}'.format(game.id, stable.id): (total_score, get_rank(game.id, total_score), ) 
            for (stable, total_score, ) in stable_scores}, 
        2 * 60 * 1000
    )

def get_stable_score_rank(game, stable_id):
    cache_key = 'stable_score_rank_{}_{}'.format(game.id, stable_id)
    current_score_rank = cache.get(cache_key)

    if current_score_rank is not None:
        return current_score_rank
    
    calculate_scores_ranks(game)
    current_score_rank = cache.get(cache_key)
    return  current_score_rank if current_score_rank is not None else (0, None, )
