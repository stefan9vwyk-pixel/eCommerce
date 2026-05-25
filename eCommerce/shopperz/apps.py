from django.apps import AppConfig
from django.db.models.signals import post_migrate


class ShopperzConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'shopperz'

    def ready(self):
        from .signals import create_groups
        # Connect the signal strictly to this app's post_migrate completion
        post_migrate.connect(create_groups, sender=self)
