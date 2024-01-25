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

            profile.first_access = True
            profile.save()
            self.stdout.write(f'Profile of {self.style.SUCCESS(user.username)} set to first access.')

        for session in Session.objects.all():
            session.delete()
