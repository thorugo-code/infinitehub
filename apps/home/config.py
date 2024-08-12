from django.apps import AppConfig


class MyConfig(AppConfig):
    name = 'apps.home'

    def ready(self):
        import apps.home.signals
