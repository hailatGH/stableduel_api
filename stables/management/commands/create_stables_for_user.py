from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

from games.models import Game
from stables.models import Stable, Runner

import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Set is_valid_at_start for Stables'

    def add_arguments(self, parser):
        parser.add_argument(
            "user_id",
            type=int,
            help="User Id for stable owner"
        )
        parser.add_argument(
            "game_id", 
            type=int, 
            help="Game Id to add stables to"
        )
        parser.add_argument(
            "count",
            type=int,
            nargs="?",
            default=5,
            help="Number of stables ot create"
        )


    def handle(self, *args, **options):
        game_id = options['game_id']
        user_id = options['user_id']
        count = options['count']

        user = User.objects.get(id=user_id)
        if user == None:
            raise CommandError(f"user with id {user_id} not found")

        game = Game.objects.get(id=game_id)
        if game == None:
            raise CommandError(f'Game with id {game_id} not found')

        if count <= 0:
            raise CommandError(f"Invalid number of stables to create ({count})")
        
        runners = Runner.objects.filter(racecard=game.racecard, coupled=False)
        print(len(runners))
        for x in range(0, count):
            stable = Stable()
            stable.user = user
            stable.game = game
            stable.save()

            stable_runners = random.sample(list(runners), 10)
            stable.runners.add(*stable_runners)
            print(f"Stable {x} created ({stable})")
        
        print(f"Done creating {count} stables")