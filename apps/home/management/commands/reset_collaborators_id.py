from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.home.models import Profile
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for user in User.objects.all():
            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                continue

            if profile.identification == 0:
                profile.identification = None
                profile.save()

            self.stdout.write(f'ID of {self.style.SUCCESS(user.username)} set to NONE.')

        for session in Session.objects.all():
            session.delete()
