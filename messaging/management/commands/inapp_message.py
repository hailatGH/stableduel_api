from django.core.management.base import BaseCommand, CommandError
from messaging.inapp_message import InAppMessage

import json

class Command(BaseCommand):
    help = 'Test InApp Messaging'

    def add_arguments(self, parser):
        parser.add_argument(
            '--channel',
            default='main-channel',
            help='message channel',
        )

        parser.add_argument(
            '--event',
            default='test',
            help='message event',
        )

        parser.add_argument(
            '--data',
            default='{"message": "Hello World!"}',
            help='data',
        )

        pass

    def handle(self, *args, **options):

        data = json.loads(options['data'])

        message = InAppMessage(options['channel'],
                               options['event'],
                               data)

        response = message.send()

        print(response)