from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Count
from stables.models import Game, Stable
User = get_user_model()

class Command(BaseCommand):
    help = 'Initially assign multiple stable entry_numbers'


    def handle(self, *args, **options):
        users = User.objects.all()

        for user in users:
            stables = Stable.objects.filter(user=user).order_by('created_at')

            if stables.count() > 1:
                #count = 1
                games = []
                for stable in stables:
                    if games.count(stable.game.id) > 0:
                        stable.entry_number = games.count(stable.game.id) + 1
                        stable.save()
                    
                    games.append(stable.game.id)

