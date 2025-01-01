class Lifespan():
    TEMPORARY              = 'temporary'
    PERSISTENT             = 'persistent'
    PERSISTENT_CONDITIONAL = 'persistent_conditional'

class Type():
    GENERAL             = 'general'
    SCRATCH             = 'scratch'
    STABLE_INCOMPLETE   = 'stable_incomplete'
    FIRST_POST          = 'first_post'
    RACE_SCORES_POSTED  = 'race_scores_posted'
    RACE_CANCELED       = 'race_canceled'
    RACE_COMPLETED      = 'race_completed'
    RACE_RESULTS_POSTED = 'race_results_posted'
    GAME_CANCELED       = 'game_canceled'
    FOLLOWED_HORSE      = 'followed_horse'

    VALUES = [
        (SCRATCH,             'Scratch'),
        (STABLE_INCOMPLETE,   'Stable Incomplete'),
        (FIRST_POST,          'First Post'),
        (RACE_SCORES_POSTED,  'Race Scores Posted'),
        (RACE_CANCELED,       'Race Canceled'),
        (RACE_COMPLETED,      'Race Completed'),
        (RACE_RESULTS_POSTED, 'Race Results Posted'),
        (GAME_CANCELED,       'Game Canceled'),
        (FOLLOWED_HORSE,      'Followed Horse')
    ]
    

class Action():
    GO_TO_STABLE      = 'go_to_stable'
    GO_TO_LEADERBOARD = 'go_to_leaderboard'
    GO_TO_RUNNER      = 'go_to_runner'
    NONE              = 'none'

    VALUES = [
        (GO_TO_STABLE,      'Go to Stable'),
        (GO_TO_LEADERBOARD, 'Go to Leaderboard'),
        (GO_TO_RUNNER,      'Go to Runner'),
        (NONE,              'None')
    ]