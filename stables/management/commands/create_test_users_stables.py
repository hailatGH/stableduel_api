import random

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from games.models import Game
from users.models import Profile
from stables.models import Stable, Runner

User = get_user_model()

class Command(BaseCommand):
    help = 'Create test accounts and give them stables'

    def add_arguments(self, parser):
        parser.add_argument(
            'game',
            type=int,
            help='Game ID for to add the stables to',
        )
        parser.add_argument(
            'user-count',
            type=int,
            help='Number of users and stables to generate',
        )

        pass

    def handle(self, *args, **options):
        game_id = options['game']
        user_count = options['user-count']

        game = Game.objects.get(pk=game_id)
        users = []

        base_user_name = 'sd-testuser'

        for x in range(0, user_count):
            user = User()
            user.first_name = 'first{}'.format(x)
            user.last_name = 'last{}'.format(x)
            user.email = 'sd-testuser{}@test.com'.format(x)
            user.auth0_id = 'invalidid-testuser-{}'.format(x)
            user.username='{}{}'.format(base_user_name, x)
            user.set_unusable_password()
            user.save()

            profile = Profile()
            profile.user = user
            profile.birthdate = '2000-02-05'
            profile.country = 'USD'
            profile.zip_code = '12345'
            profile.stable_name = '{}{}'.format(base_user_name, x)

            profile.save()

            print("USER CREATED: {}".format(user))
            users.append(user)

        runners = Runner.objects.filter(racecard=game.racecard, coupled=False)

        for user in users:
            stable = Stable()
            stable.user = user
            stable.game = game
            stable.save()
            runners = random.sample(list(runners), 10)
            stable.runners.add(*runners)
            print("STABLE CREATED {}:".format(stable))
        
        print("Done creating {} users and stables".format(user_count))



