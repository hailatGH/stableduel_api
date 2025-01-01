from django.core.management.base import BaseCommand, CommandError
from racecards.notifications import RaceScoresPostedNotification

class Command(BaseCommand):
    help = 'Test Race Scores Posted Notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            'user_ids',
            type=str,
            help='lists of user ids',
        )

        parser.add_argument(
            'race_number',
            type=int,
            help='Race Number',
        )

        pass

    def handle(self, *args, **options):

        user_ids = [uid.strip() for uid in options['user_ids'].split(',')]

        notification = RaceScoresPostedNotification(user_ids, options['race_number'])

        print(notification.send())