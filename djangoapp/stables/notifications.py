from notifications.push_notifications import PushToUsersNotification
from notifications.constants import Type, Action, Lifespan

class ScratchedNotification(PushToUsersNotification):

    title = "Scratched"
    message = "A runner in your stable has scratched"

    def __init__(self, user_ids, runner, stable):
        super(ScratchedNotification, self).__init__(
            Type.SCRATCH,
            Action.GO_TO_STABLE,
            Lifespan.PERSISTENT,
            user_ids,
            stable.id
        )
        
        self.setData({'runner': runner.id, 'racecard': runner.racecard.id, 'stable':stable.id})

class IncompleteStableNotification(PushToUsersNotification):

    title = "Stable Incomplete"
    message = "Don't miss out! The first race is starting soon but your stable is incomplete."

    def __init__(self, user_ids, stable):
        super(IncompleteStableNotification, self).__init__(
            Type.STABLE_INCOMPLETE,
            Action.GO_TO_STABLE,
            Lifespan.TEMPORARY,
            user_ids,
            stable.id
        )

        self.setData({'stable':stable.id})
