from django.conf import settings
import pusher
import logging

def has_valid_settings():
    return len(settings.PUSHER_APP_ID) > 0 and \
           len(settings.PUSHER_APP_KEY) > 0 and \
           len(settings.PUSHER_APP_SECRET) > 0

class InAppMessage():
    
    def __init__(self, channel, event, data):

        self.logger = logging.getLogger(__name__)

        self.client = None

        self.channel = channel
        self.event = event
        self.data = data

        if has_valid_settings():
            self.client = pusher.Pusher(
                app_id=settings.PUSHER_APP_ID,
                key=settings.PUSHER_APP_KEY,
                secret=settings.PUSHER_APP_SECRET,
                cluster=settings.PUSHER_APP_CLUSTER,
                ssl=True
            )

    def send(self):

        self.logger.info("Sending InApp Message: Channel: {} Event: {} Data: {}".format(self.channel, self.event, str(self.data)))
        
        if self.client:
            self.logger.info("    Message Sent")
            return self.client.trigger(self.channel,
                                       self.event,
                                       {'data': self.data})
        
        return None