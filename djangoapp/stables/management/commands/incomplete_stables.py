from django.core.management.base import BaseCommand, CommandError

from stables.models import Game
from stables.models import calculate_stable_is_valid

class Command(BaseCommand):
    help = 'Set is_valid_at_start for Stables'

    def add_arguments(self, parser):
        parser.add_argument('game_number', type=int)


    def handle(self, *args, **options):
        game_id = options['game_number']
        g = Game.objects.get(pk=game_id)
        calculate_stable_is_valid(g)