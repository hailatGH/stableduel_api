from notifications.push_notifications import PushToUsersNotification, PushToInterestsNotification
from notifications.constants import Type, Action, Lifespan

class GameCanceledNotification(PushToInterestsNotification):

    title = "Game Canceled"
    message = "Game canceled"

    def __init__(self, game):

        interests = ['game-' + str(game.id)]

        super(GameCanceledNotification, self).__init__(
            Type.GAME_CANCELED,
            Action.NONE,
            Lifespan.TEMPORARY,
            interests
        )

class FirstPostNotification(PushToInterestsNotification):
    title = '30 Minutes to first post'
    message = 'The first race is about to start. You have about 30 more minutes to make changes to your stable'

    def __init__(self, game):

        interests = ['game-' + str(game.id)]

        super().__init__(
            Type.FIRST_POST,
            Action.GO_TO_STABLE,
            Lifespan.TEMPORARY,
            interests
        )