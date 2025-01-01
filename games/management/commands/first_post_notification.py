from django.core.management.base import BaseCommand, CommandError
from games.notifications import FirstPostNotification
from games.models import Game

class Command(BaseCommand):
    help = 'Test First Post Notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            'game_id',
            type=str,
            help='ID of game',
        )

        pass

    def handle(self, *args, **options):

        game = Game.objects.get(id=options['game_id'])

        notification = FirstPostNotification(game)

        print(notification.send())