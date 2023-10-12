from notifications.push_notifications import PushToUsersNotification
from notifications.push_notifications import PushToInterestsNotification
from notifications.constants import Type, Action, Lifespan
from racecards.models import Track


class FirstPostNotification(PushToUsersNotification):

    title = "First Post Approaching"
    message = "First post is happening soon"

    def __init__(self, user_ids):
        super(FirstPostNotification, self).__init__(
            Type.FIRST_POST,
            Action.GO_TO_LEADERBOARD,
            Lifespan.TEMPORARY,
            user_ids
        )

class RaceScoresPostedNotification(PushToUsersNotification):

    title = "Race Scores Posted"
    message = "New race scores have been posted"

    def __init__(self, user_ids, race_number, stable):
        super(RaceScoresPostedNotification, self).__init__(
            Type.RACE_SCORES_POSTED,
            Action.GO_TO_LEADERBOARD,
            Lifespan.TEMPORARY,
            user_ids
        )

        self.setData({'race_number': race_number})

class RaceCanceledNotification(PushToInterestsNotification):

    title = "Race Canceled"
    message = "Today's races at {} have been canceled. Check back later for future games"

    def __init__(self, trackname, interests):
        self.message = self.message.format(trackname)
        super(RaceCanceledNotification, self).__init__(
            Type.RACE_CANCELED,
            Action.NONE,
            Lifespan.TEMPORARY,
            interests
        )

class RaceResultsNotification(PushToUsersNotification):

    title = "Race Results"
    message = "New race results are available"

    def __init__(self, user_ids, stable):
        super(RaceResultsNotification, self).__init__(
            Type.RACE_RESULTS_POSTED,
            Action.NONE,
            Lifespan.PERSISTENT,
            user_ids
        )

        