from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _
from .utils import get_user_rank

class User(AbstractUser):
    auth0_id = models.CharField(max_length=100, blank=True, db_index=True)
    
    email = models.EmailField(
        verbose_name='email address',
        max_length=254,
        unique=True,
    )
    
    gamstop_exclude = models.BooleanField(default=False)
    def get_short_name(self):
        return "{} {}".format(self.first_name, self.last_name)

    @property
    def score(self):
        score_rank = get_user_rank(self)
        score, _ = score_rank
        return score
    
    @property
    def rank(self):
        score_rank = get_user_rank(self)
        _, rank = score_rank
        return rank

class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    birthdate = models.DateField()
    country = models.CharField(
        max_length=3,
        help_text=_("Three digit country code. See https://en.wikipedia.org/wiki/ISO_3166-1#Current_codes"),
        default="USA"
    )

    zip_code = models.CharField(
        max_length=15,
        help_text=_("Five digit zip code or postal code")
    )

    stable_name = models.CharField(
        max_length=50,
        help_text=_("Name of the users stable"),
        unique=True
    )

    unique_stable_name = models.CharField(
        max_length=50,
        help_text=_("Autoset field to ensure stable name is unique in case insensitive manner"),
        unique=True,
        db_index=True,
    )

    is_admin = models.BooleanField(default=False)
    
    deposit_limit = models.IntegerField(default=1)


    def __init__(self, *args, **kwargs):
        super(Profile, self).__init__(*args, **kwargs)
        self.__original_stable_name = self.stable_name

    def save(self, *args, **kwargs):
        self.unique_stable_name = self.stable_name.lower()

        if self.stable_name != self.__original_stable_name:
            #User has updated their stable name so they will lose all existing Stable Points
            #TODO - Include these in audit/history
            self.user.stablepoint_set.all().delete()
            
        super().save(*args, **kwargs)
        self.__original_stable_name = self.stable_name




        
