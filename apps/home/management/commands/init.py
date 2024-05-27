from django.core.management.base import BaseCommand
from apps.home.models import Project, Client
from apps.authentication.models import AuthEmail
from django.contrib.auth.models import User
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        # Delete all sessions
        self.stdout.write(f'Deleting sessions...', ending=' ')
        for session in Session.objects.all():
            session.delete()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))
