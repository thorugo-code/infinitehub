from django.core.management.base import BaseCommand
from apps.home.models import Task


class Command(BaseCommand):
    help = 'Update database'

    def handle(self, *args, **options):
        self.stdout.write('Not implemented yet.')
