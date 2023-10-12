from django.core.management.base import BaseCommand, CommandError
from racecards.notifications import RaceResultsNotification

class Command(BaseCommand):
    help = 'Test Race Results Notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            'user_ids',
            type=str,
            help='lists of user ids',
        )

        pass

    def handle(self, *args, **options):

        user_ids = [uid.strip() for uid in options['user_ids'].split(',')]

        notification = RaceResultsNotification(user_ids)

        print(notification.send())