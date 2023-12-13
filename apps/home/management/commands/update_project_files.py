from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.home.models import Profile, UploadedFile


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for file in UploadedFile.objects.all():
            if file.client is None:
                file.save()

                if file.client is None:
                    continue

                self.stdout.write(
                    f'File client updated: {self.style.SUCCESS(file.file.name)}')
