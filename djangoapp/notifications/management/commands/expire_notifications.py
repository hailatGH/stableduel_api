from django.core.management.base import BaseCommand, CommandError

from notifications.models import Notification

class Command(BaseCommand):
    help = 'Expire all existing Notification objects'


    def handle(self, *args, **options):
        #Expire all of the existing notifications so they aren't returned in the API
        #This also expires notifications from contests past since they haven't been
        #marked as such already.
        notifications = Notification.objects.filter(expired=False)
        for notification in notifications:
                notification.expired = True
                notification.save()
    
