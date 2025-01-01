from collections import defaultdict
from decimal import Decimal, ROUND_HALF_UP
from enum import Enum

from django.db import models
from django.db.models import Count
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django_redis import get_redis_connection
from django.db.models import Q, Max
from django.contrib.postgres.fields import JSONField
from rest_framework.exceptions import APIException
from datetime import datetime

from games.models import Game
from racecards.models import Racecard
from wagering.chrims_api import update_bet, cancel_bet
from stables.notifications import ScratchedNotification
from softdelete.models import SoftDeleteModel

from .utils import get_salary

User = get_user_model()

class BetFailed(APIException):
    status_code = 500
    default_detail = 'Creating a bet failed for this stable.'
    default_code = 'bet_failed'

class Runner(models.Model):
    racecard = models.ForeignKey(Racecard, on_delete=models.CASCADE, db_index=True, null=True)
    external_id = models.CharField(max_length=25, null=True, blank=True)
    name = models.CharField(max_length=200)
    scratched = models.BooleanField(default=False)
    scratched_datetime = models.DateTimeField(null=True, blank=True)
    race_number = models.IntegerField(null=True)
    post_position = models.IntegerField(null=True)
    program_number = models.CharField(max_length=25, blank=True, null=True)
    odds = models.CharField(max_length=10, null=True)
    trainer = models.CharField(max_length=200, blank=True, null=True)
    jockey = models.CharField(max_length=200, blank=True, null=True)
    pedigree = JSONField(default=[], blank=True)
    owner = models.CharField(max_length=500, blank=True, null=True)
    finish = models.IntegerField(null=True, blank=True)
    coupled = models.BooleanField(default=False)
    coupled_indicator = models.CharField(max_length=10, blank=True, null=True)
    lengths_behind = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    lengths_ahead = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2)
    disqualified = models.BooleanField(default=False)
    score = models.DecimalField(null=True, blank=True, max_digits=5,decimal_places=2)
    career_stats = JSONField(default=[], blank=True)
    past_performance = JSONField(default=[], blank=True)
    workouts = JSONField(default=[], blank=True)
    #Update the default value to a NULL
    custom_stats = JSONField(default=None, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def margin(self):
        margin = 0

        if self.lengths_ahead is None and self.lengths_behind is None:
            return None

        if self.finish == 1:
           margin = float(self.lengths_ahead) / 100
        #else:
           #margin -= float(self.lengths_behind) / 100

        return margin

    @property
    def points(self):
        return get_runner_points(self.finish)
   
    @property
    def salary(self):
        return get_salary(self.odds)

    @property
    def stable_count(self):
        return cache.get('runner_{}_stable_count'.format(self.id), None)
    
    @property
    def total_stables(self):
        return cache.get('racecard_{}_total_stables'.format(self.racecard.id), None)
    
    # def save(self, *args, **kwargs):
    #     #When creating a new 
    #     if self.pk == None: # Only execute this logic during update
    #         self.scratched = True
    #         self.scratched_datetime = datetime.now()
    #         stables = self.stable_set.all()
    #         for stable in stables:
    #             user = [stable.user.auth0_id]
    #             #Send the notification to every game that includes this racecard that contains the specified runner
    #             #Create a list with a single user because that's what pusher beams expects
    #             pn = ScratchedNotification(user, self, stable)
    #             pn.send()

    #     super().save(*args, **kwargs)

        

    def __str__(self):
        return "ID: {} NAME: {}".format(self.id, self.name)
        
class Stable(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    runners = models.ManyToManyField(Runner)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_valid_at_start = models.NullBooleanField(null=True, db_index=True)
    scratch_limit_reached = models.BooleanField(default=False)
    scratches_at_finish = models.BooleanField(default=False)
    is_submitted = models.BooleanField(default=False)
    stable_count_at_finish = models.IntegerField(null=True, blank=True)
    entry_number = models.PositiveIntegerField(default=1)
    
    replaced_scratches_count = models.PositiveIntegerField(default=0)

    UNKNOWN = 'UNKNOWN'
    NOT_STARTED_VALID = 'NOT_STARTED_VALID'
    NOT_STARTED_INVALID = 'NOT_STARTED_INVALID'
    STARTED_VALID = 'STARTED_VALID'
    STARTED_NEEDS_SCRATCH_REPLACEMENT= 'STARTED_NEEDS_SCRATCH_REPLACEMENT'
    STARTED_IS_REPLACING_SCRATCH = 'STARTED_IS_REPLACING_SCRATCH'
    FINAL_RESULTS_PENDING = 'FINAL_RESULTS_PENDING'
    FINISHED = 'FINISHED'
    STARTED_DISQUALIFIED = 'STARTED_DISQUALIFIED'
    FINISHED_DISQUALIFIED = 'FINISHED_DISQUALIFIED'

    @property
    def score(self):
        if self.is_valid_at_start == False or self.game.game_state == Game.CANCELLED:
            return 0

        cache_key = 'stable_score_rank_{}_{}'.format(self.game_id, self.id)
        current_score_rank = cache.get(cache_key)

        if current_score_rank is not None:
            score, _ = current_score_rank
            return score

        return 0
    
    @property
    def rank(self):
        if self.is_valid_at_start == False or self.game.game_state == Game.CANCELLED:
            return None

        cache_key = 'stable_score_rank_{}_{}'.format(self.game_id, self.id)
        current_score_rank = cache.get(cache_key)

        if current_score_rank is not None:
            _, rank = current_score_rank
            return rank

        return None

    def save(self, *args, **kwargs):
        #When creating a new 
        print('====')
        print(self.pk)
        if self.pk == None:
            if Stable.objects.filter(user=self.user, game=self.game).count() > 0:
                self.entry_number = Stable.objects.filter(user=self.user,game=self.game).aggregate(max_id=Max("entry_number")).get("max_id",0) + 1
            else:
                self.entry_number = 1

        super().save(*args, **kwargs)

        bet = update_bet(self)
        
        if bet.bet_submitted == False:
            self.delete()
            raise BetFailed()
    
    def delete(self):
        cancel_bet(self)
        super().delete()

def get_stable_count(stable):
    """
    Gets the total number of runners in a stable, including coupled entries as 1
    """
    num_runners = 0
    coupled_runners = defaultdict(list)
    runners = stable.runners.all()
    for runner in runners:
        if runner.coupled == False:
            num_runners += 1
        else:
            coupled_runners[runner.coupled_indicator + '-' + str(runner.race_number)].append(runner)

    #If we have any coupled runners, count the whole group as 1
    for coupled_indicator_value in coupled_runners:
        num_runners += 1

    return num_runners

def get_stable_scratched_count(stable):
    num_scratched = 0
    runners = stable.runners.all()

    coupled_runners = defaultdict(list)
    for runner in runners:
        if(runner.coupled == True):
            coupled_runners[runner.coupled_indicator].append(runner)

    for runner in runners:
        scratched = False
        if(runner.coupled == True):
            bothScratched = True
            # Only add if all coupled runners are scratched
            for coupled_runner in coupled_runners[runner.coupled_indicator]:
                if(coupled_runner.scratched == False):
                    bothScratched = False
            if bothScratched == True:
                scratched = True
        else:
            scratched = runner.scratched

        if scratched == True:
            num_scratched += 1

    return num_scratched

def get_runner_points(position):
    points = 0
    if position is None:
        return 0

    if position == 1:
        points = 60
    else:
        if position == 2:
            points += 40
        elif position == 3:
            points += 30
        elif position == 4:
            points += 20
        elif position == 5:
            points += 10
    return points

def invalid_stables(game):
    stables = Stable.objects.filter(game=game).annotate(runner_count=Count('runners')).prefetch_related('runners').select_related('user')
    invalid_stables = []
    for stable in stables:
        if get_stable_count(stable) < 10:
            invalid_stables.append(stable)
    
    return invalid_stables

def calculate_stable_is_valid(game):
    stables = Stable.objects.filter(game=game).annotate(runner_count=Count('runners')).prefetch_related('runners')
    valid_stables_count = 0
    invalid_stables_count = 0
    for stable in stables:
        if get_stable_count(stable) < 10 or get_stable_scratched_count(stable) > 3 or stable.is_submitted == False:
            stable.is_valid_at_start = False
            invalid_stables_count += 1
        else:
            stable.is_valid_at_start = True
            valid_stables_count += 1
        stable.save()
    return (valid_stables_count, invalid_stables_count)

def get_stable_score(stable):
    """
    Gets the total score for all runners in a stable
    """
    runners = stable.runners.all()
    total_coupled_score = 0
    coupled_runners = defaultdict(list)
    for runner in runners:
        if runner.coupled:
            coupled_runners[runner.coupled_indicator + '-' + str(runner.race_number)].append(runner)

    for coupled_indicator_value in coupled_runners:
        if(coupled_runners[coupled_indicator_value][0].score != None):
            total_coupled_score += coupled_runners[coupled_indicator_value][0].score


    total_score_not_coupled = sum([runner.score for runner in runners if runner.score is not None and not runner.coupled])
    total_score = total_score_not_coupled + total_coupled_score
    total_score = format_score(total_score)

    if stable.is_valid_at_start and not stable.scratch_limit_reached:
        scratches = get_stable_scratched_count(stable)
        if scratches > 3:
            stable.scratch_limit_reached = True
            stable.save()

    return (stable, total_score, )

def get_rank(game, total_score):
    """
    Gets the rank for a stable based on a given score
    """

    conn = get_redis_connection('default')
    rank = conn.zcount('stable_scores_{}'.format(game.id),'({}'.format(float(total_score)), '+inf')

    return rank + 1 if rank is not None else None

def format_score(score):
    new_score = Decimal(Decimal(score).quantize(Decimal('.01'), rounding=ROUND_HALF_UP))
    return int(new_score) if new_score % 1 == 0 else new_score

def calculate_scores_ranks(game):
    """
    Totals score for all stables and creates a set in redis to use for ranking the scores.
    The scores/ranks for a stable are cached for 2 minutes
    """

    conn = get_redis_connection('default')

    stables = (Stable.objects
        .filter(game=game)
        .filter(~Q(is_valid_at_start=False))
        .annotate(runner_count=Count('runners'))
        .filter(Q(is_valid_at_start=True) | Q(runner_count__gte=10))
        .prefetch_related('runners'))

    stable_scores = [get_stable_score(stable) for stable in stables]
    conn.delete('stable_ranks_{}'.format(game.id))
    conn.delete('stable_scores_{}'.format(game.id))

    if not len(stable_scores) > 0:
        return

    conn.zadd('stable_ranks_{}'.format(game.id), {str(format_score(total_score)): float(total_score) for (_, total_score,) in stable_scores})
    conn.zadd('stable_scores_{}'.format(game.id), {"{}".format(stable.id): float(total_score) for (stable, total_score,) in stable_scores})
    
    cache.set_many(
        { 'stable_score_rank_{}_{}'.format(game.id, stable.id): (total_score, get_rank(game, total_score), ) 
            for (stable, total_score, ) in stable_scores}, 
        None
    )
    print("ranks updated")

def get_stable_score_rank(game, stable_id):
    cache_key = 'stable_score_rank_{}_{}'.format(game.id, stable_id)

    calculate_scores_ranks(game)
    current_score_rank = cache.get(cache_key)
    return  current_score_rank if current_score_rank is not None else (0, None, )

def get_stable_score_count(game):
    conn = get_redis_connection('default')
    count = conn.zcount('stable_scores_{}'.format(game.id),'-inf', '+inf')
    if count is None:
        calculate_scores_ranks(game)
    else:
        return count

    count = conn.zcount('stable_scores_{}'.format(game.id),'-inf', '+inf')
    return count

def get_stable_ids(game, top, bottom):
    conn = get_redis_connection('default')
    ids = conn.zrevrange('stable_scores_{}'.format(game.id), bottom, top-1)
    print("game: {}".format(game))
    print("top: {}".format(top))
    print("bottom: {}".format(bottom))
    print("ids: {}".format(ids))

    if ids is None:
        calculate_scores_ranks(game)
    else:
        return [int(id) for id in ids]

    ids = conn.zrevrange('stable_scores_{}'.format(game.id), bottom, top-1)
    return [int(id) for id in ids]

