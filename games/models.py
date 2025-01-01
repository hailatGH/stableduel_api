from django.contrib.postgres.fields import JSONField
from django.core.cache import cache
from django.db import models
from racecards.models import Racecard
from users.models import User
from wagering.chrims_api import get_contest_pool, update_contest
from django.core.validators import MinValueValidator

from . import validators


def Banner_Images(instance, filename):
    return '/'.join(['Banner_Images', str(instance.name) + "_" + str(filename)])
  
class Game(models.Model):
    class Meta:
        ordering = ['-id']
    
    racecard = models.ForeignKey(Racecard, on_delete=models.CASCADE)
    params = JSONField(default={'a': 1})
    name = models.CharField(max_length=200)
    started = models.BooleanField(default=False)
    finished = models.BooleanField(default=False)
    archived = models.BooleanField(default=False)
    published = models.BooleanField(default=True)
    notification_sent = models.BooleanField(default=False)
    winner_limit = models.IntegerField(default=1, verbose_name="Players Paid")
    stable_limit = models.IntegerField(default=-1)
    runner_limit = models.IntegerField(default=10)
    salary_cap = models.IntegerField(default=50000)
    entry_fee = models.IntegerField(default=0)
    is_private = models.BooleanField(default=False)
    payout_projections = models.TextField(null=True, blank=True)
    OPEN = 'OPEN'
    LIVE = 'LIVE'
    RESULTS_PENDING = 'RESULTS_PENDING'
    FINISHED = 'FINISHED'
    CANCELLED = 'CANCELLED'

    GAME_STATE_CHOICES = (
        (OPEN, 'Open'),
        (LIVE, 'Live'),
        (RESULTS_PENDING, 'Results Pending'),
        (FINISHED, 'Finished'),
        (CANCELLED, 'Cancelled'),
    )
    game_state = models.CharField(max_length=20, choices=GAME_STATE_CHOICES, default=OPEN)

    contest_amount = models.IntegerField(default=0, verbose_name="Guaranteed Pool")
    commission_percent = models.IntegerField(default=0)
    entry_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    private_members = models.ManyToManyField(User, through="GameUser")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        update_contest(self)
    
    def __str__(self):
        return self.name

    def get_pool(self):
        cache_key = "game_pool_{}".format(self.id)
        pool = cache.get(cache_key)
        if pool is None:
            #Get the pool value from the API
            try:
                pool = int(get_contest_pool(self))
                if pool is None:
                  return 0
                else:
                    cache.set(cache_key, pool, 60 * 10)
                    return pool
            except: 
                return 0
        
        return int(pool)

class GameUser(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

class GameExcludeUsers(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    

class Banner(models.Model):
    class Meta:
        ordering = ['-id']

    VISIBLE="VISIBLE"
    HIDDEN="HIDDEN"

    VisibilityChoices= (
        [VISIBLE, "Visible"],
        [HIDDEN, "Hidden"]
    )

    name = models.CharField(null=False, blank=True, max_length=256)
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)
    link = models.CharField(null=False, blank=True, max_length=256)
    visibility = models.CharField(choices=VisibilityChoices, max_length=20, default=VISIBLE)
    image = models.ImageField(null=False, blank=True, upload_to=Banner_Images, validators=[validators.validate_banner_image], help_text="Image height should not exceed 85px")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.pk}-{self.name}-{self.created_at.date()}/{self.updated_at.date()}"

class GamePayout(models.Model):
    game = models.ForeignKey(Game, on_delete=models.CASCADE, db_index=True)

    position = models.IntegerField(default=1, verbose_name="Finish Position", validators=[MinValueValidator(1)])
    value = models.DecimalField(default=0, verbose_name="Payout", decimal_places=2, max_digits=12, validators=[MinValueValidator(0)])
