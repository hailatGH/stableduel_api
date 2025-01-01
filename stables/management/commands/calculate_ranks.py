from django.core.management.base import BaseCommand, CommandError, CommandParser

from stables.models import Game
from stables.models import calculate_scores_ranks

class Command(BaseCommand):
    help = 'Test Incomplete Stable Notifications'

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('game_id', type=int, help="Game ID to calculate ranks for")
        pass

    def handle(self, *args, **options):
        game_id = options['game_id']
        try:
            game = Game.objects.get(id=game_id)
            calculate_scores_ranks(game)
        except Game.DoesNotExist:
            raise CommandError("Game does not exist")

