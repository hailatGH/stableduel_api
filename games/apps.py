from django.apps import AppConfig


class GamesAppConfig(AppConfig):
    name = "games"
    verbose_name = "Games"

    def ready(self):
        import games.signals
