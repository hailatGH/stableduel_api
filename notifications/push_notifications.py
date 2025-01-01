from pusher_push_notifications import PushNotifications as PushNotificationsBase
from pusher_push_notifications import PusherAuthError, PusherMissingInstanceError, PusherServerError, PusherValidationError
from django.conf import settings
import logging

from .tasks import store_persistent_user_notifications
from .constants import Lifespan

MAX_USERS_PER_REQUEST = 1000

class PushNotifications:

    def __init__(self):

        self.logger = logging.getLogger(__name__)

        if len(settings.PUSHERBEAMS_INSTANCE_ID) > 0 and len(settings.PUSHERBEAMS_SECRET_KEY) > 0:
            self.client = PushNotificationsBase(
                instance_id=settings.PUSHERBEAMS_INSTANCE_ID,
                secret_key=settings.PUSHERBEAMS_SECRET_KEY,
            )
        else:
            self.client = None

    '''
      Send push notification to all devices subscribing to given interests
    '''
    def pushToInterests(self, interests, title, message, data=None):

        response = None

        if self.client != None:
            publish_body = self.generatePublishBody(title, message, data)
            response = self.sendToInterest(interests, publish_body)
            
        return response

    '''
      Send push notification to given user ids

      Note: user_ids is list of user auth0 ids
              
    '''
    def pushToUsers(self, user_ids, title, message, data=None):
        response = None

        if self.client != None:

            publish_body = self.generatePublishBody(title, message, data)

            if len(user_ids) <= MAX_USERS_PER_REQUEST:
                response = self.sendToUsers(user_ids, publish_body)
            else:
                start = 0
                for index in range(0, len(user_ids), MAX_USERS_PER_REQUEST):

                    end = index + MAX_USERS_PER_REQUEST
                    users = user_ids[start:end]
                    start = end

                    response = self.sendToUsers(users, publish_body)

                    if not response:
                        break

        return response

    def sendToInterest(self, interests, body):
        try:
            response = self.client.publish_to_interests(
                interests=interests,
                publish_body=body
            )
        except (PusherAuthError, PusherMissingInstanceError, PusherServerError, PusherValidationError) as e:
            self.logger.error("Failed to send request to Pusher:  %s", str(e))
            response = None

        except (TypeError, ValueError) as e:
            self.logger.error("Failed to send request to Pusher:  %s", str(e))
            response = None

        return response

    def sendToUsers(self, user_ids, body):
        try:
            response = self.client.publish_to_users(
                        user_ids=user_ids,
                        publish_body=body
                    )
        except (PusherAuthError, PusherMissingInstanceError, PusherServerError, PusherValidationError) as e:
            self.logger.error("Failed to send request to Pusher:  %s", str(e))
            response = None

        except (TypeError, ValueError) as e:
            self.logger.error("Failed to send request to Pusher:  %s", str(e))
            response = None

        return response

    def generatePublishBody(self, title, message, data):

        return {
                # iOS message
                'apns': {
                    'aps': {
                        'alert': message,
                        'badge': 1,
                        'data': data
                    }
                },
                # Android message
                'fcm': {
                    'notification': {
                        'title': title,
                        'body': message,
                        'data': data
                    }
                }
            }

class PushToInterestsNotification():

    title = ''
    message = ''

    def __init__(self, notiftype, action, lifespan, interests):

        self.interests = interests

        self.data = {
            'type': notiftype,
            'action': action,
            'lifespan': lifespan
        }

        self.notifications = PushNotifications()

    def setData(self, data):

        if self.data:
            self.data['data'] = data

    def send(self):

        if self.notifications:
            return self.notifications.pushToInterests(self.interests, self.title, self.message, self.data)

        return None

class PushToUsersNotification():

    title = ''
    message = ''

    def __init__(self, notiftype, action, lifespan, user_ids, stable_id=None, runner_id=None):

        self.user_ids = user_ids
        self.notiftype = notiftype
        self.action = action
        self.stable_id = stable_id
        self.runner_id = runner_id
        self.lifespan = lifespan

        self.data = {
            'type': notiftype,
            'action': action,
            'stable_id':stable_id,
            'runner_id':runner_id,
            'lifespan': lifespan
        }

        self.notifications = PushNotifications()

    def setData(self, data):

        if self.data:
            self.data['data'] = data

    def send(self):

        if self.lifespan != Lifespan.TEMPORARY:
            store_persistent_user_notifications.delay(self.user_ids,
                                                      self.title,
                                                      self.message,
                                                      self.action,
                                                      self.stable_id,
                                                      self.runner_id,
                                                      self.notiftype)

        if self.notifications:
            return self.notifications.pushToUsers(self.user_ids, self.title, self.message, self.data)

        return None
