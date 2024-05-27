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

        # Update profile qr code
        self.stdout.write(f'Updating profile qr code...', ending=' ')
        for user in User.objects.all():
            if user.is_active:
                user.profile.generate_qrcode()
            elif user.profile.qrcode:
                user.profile.qrcode.delete(save=False)
                user.profile.qrcode = None
                user.profile.save()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))
