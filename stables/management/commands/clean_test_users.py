import random

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from games.models import Game
from users.models import Profile
from stables.models import Stable

User = get_user_model()

class Command(BaseCommand):
    help = 'Remove test accounts'


    def handle(self, *args, **options):
        base_user_name = 'sd-testuser'
        users = User.objects.filter(username__startswith=base_user_name)
        profiles = Profile.objects.filter(stable_name__startswith=base_user_name)
        user_count = len(users)

        stables = Stable.objects.filter(user__in=users)
        stables.delete()
        users.delete()
        profiles.delete()
        
        print("Done deleting {} users and stables".format(user_count))



