from django.core.management.base import BaseCommand, CommandError
from stables.notifications import ScratchedNotification
from stables.models import Runner

class Command(BaseCommand):
    help = 'Test Scratched Notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            'user_ids',
            type=str,
            help='lists of user ids',
        )

        parser.add_argument(
            'runner',
            type=int,
            help='ID of scratched runner',
        )

        pass

    def handle(self, *args, **options):

        user_ids = [uid.strip() for uid in options['user_ids'].split(',')]

        runner = Runner.objects.get(id=options['runner'])

        notification = ScratchedNotification(user_ids, runner)

        print(notification.send())