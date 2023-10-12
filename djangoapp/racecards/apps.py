from django.apps import AppConfig


class RacecardsAppConfig(AppConfig):
    name = "racecards"
    verbose_name = "Racecards"

    def ready(self):
        import racecards.signals