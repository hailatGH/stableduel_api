from notifications.push_notifications import PushToUsersNotification
from notifications.push_notifications import PushToInterestsNotification
from notifications.constants import Type, Action, Lifespan
from stables.models import Runner
import datetime


class FollowsHorseNotification(PushToUsersNotification):
    title = "Followed Horse"
    message = "{} was added as a final entry in race {} at {} on {}. Get in the Game!"
        
    def __init__(self, user_ids, runner, racecard):
        self.message = self.message.format(runner.name,runner.race_number,racecard.track.name, racecard.race_date.strftime('%A') )
        super(FollowsHorseNotification, self).__init__(
            Type.FOLLOWED_HORSE,
            Action.GO_TO_RUNNER,
            Lifespan.PERSISTENT,
            user_ids,
            None,
            runner.id
        )
        

