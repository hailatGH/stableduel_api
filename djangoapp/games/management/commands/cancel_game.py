from django.core.management.base import BaseCommand, CommandError
from games.models import Game
from stables.models import Stable

from wagering.chrims_api import update_contest, cancel_bet

class Command(BaseCommand):
    help = 'Cancel a game. Mark the conest as cancelled and refund all existing bets. Delete stables for the game.'

    def add_arguments(self, parser):
        parser.add_argument(
            'game_id',
            type=str,
            help='ID of game',
        )

        pass

    def handle(self, *args, **options):
        game = Game.objects.get(id=options['game_id'])

        stables = Stable.objects.filter(game=game)
        for stable in stables:
            # Delete the stable and submit a bet refund
            print('Cancelling bet for stable: {}'.format(stable.id))
            cancel_bet(stable)

        print('Updating Game')
        game.published = False
        game.archived = True
        game.game_state = Game.CANCELLED
        game.save()
        update_contest(game, 'contestIsCancelled')

        print('game has been cancelled')