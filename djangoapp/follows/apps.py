from django.apps import AppConfig


class FollowsConfig(AppConfig):
    name = "follows"
    verbose_name = "Follows"

    def ready(self):
        import follows.signals


