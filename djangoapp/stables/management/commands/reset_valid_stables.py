from django.core.management.base import BaseCommand

from stables.models import Game, Stable

class Command(BaseCommand):
    help = 'Set is_valid_at_start for Stables'

    def add_arguments(self, parser):
        parser.add_argument('game_number', type=int)


    def handle(self, *args, **options):
        game_id = options['game_number']
        game = Game.objects.get(pk=game_id)
        stables = Stable.objects.filter(game=game)
        stables.update(is_valid_at_start=None)