from django.core.management.base import BaseCommand, CommandError
from notifications.push_notifications import PushNotifications

class Command(BaseCommand):
    help = 'Test Push Notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--interests',
            default='main',
            help='lists of interests',
        )

        parser.add_argument(
            '--title',
            default='Hello',
            help='Notification title',
        )

        parser.add_argument(
            '--message',
            default='Hello World!',
            help='Notification message',
        )

        pass

    def handle(self, *args, **options):

        interests = options['interests'].split(',')

        pn = PushNotifications()

        response = pn.pushToInterests(interests, options['title'], options['message'])

        print(response)