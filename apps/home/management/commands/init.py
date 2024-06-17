from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from apps.home.models import Bill


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        # Delete all sessions
        self.stdout.write(f'Deleting sessions...', ending=' ')
        for session in Session.objects.all():
            session.delete()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))

        self.stdout.write(f'Deleting bills...', ending=' ')
        for bill in Bill.objects.all():
            bill.delete()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))
