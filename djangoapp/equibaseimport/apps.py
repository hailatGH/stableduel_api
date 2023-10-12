from django.apps import AppConfig


class RacecardsAppConfig(AppConfig):
    name = "equibaseimport"
    verbose_name = "Equibase Import"

    # def ready(self):
    #     import equibaseimport.signals
