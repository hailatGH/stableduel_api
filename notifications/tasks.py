from celery import shared_task
from .models import Notification
from users.models import User

@shared_task
def store_persistent_user_notifications(users, title, message, action, stable_id, runner_id, notif_type):

    existing_notifications = Notification.objects.filter(user__auth0_id__in=users,
                                                         title=title,
                                                         message=message,
                                                         action=action,
                                                         stable_id=stable_id,
                                                         runner_id=runner_id,
                                                         notif_type=notif_type).values_list('user__id', flat=True)
                                                         
    users = User.objects.filter(auth0_id__in=users).exclude(id__in=existing_notifications)

    notifications = []
    for user in users:
        notifications.append(Notification(
            user = user,
            title = title,
            message=message,
            action=action,
            stable_id=stable_id,
            runner_id=runner_id,
            notif_type=notif_type
        ))
    
    Notification.objects.bulk_create(notifications)

    return True