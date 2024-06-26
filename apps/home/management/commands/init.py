from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from apps.home.models import Project


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        # Delete all sessions
        self.stdout.write(f'Deleting sessions...', ending=' ')
        for session in Session.objects.all():
            session.delete()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))

        # Update Projects
        self.stdout.write(f'Updating projects...', ending=' ')
        for project in Project.objects.all():
            project.save()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))
