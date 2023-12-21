from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.home.models import Profile


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for user in User.objects.all():
            profile, created = Profile.objects.get_or_create(user=user)
            if created:
                self.stdout.write(f'Profile created for user: {self.style.SUCCESS(user.username)}')
            elif not profile.slug:
                profile.save(slug=True)
                self.stdout.write(f'Profile slug created for user: {self.style.SUCCESS(user.username)}')