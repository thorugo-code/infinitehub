from django.core.management.base import BaseCommand
from apps.home.models import UploadedFile


class Command(BaseCommand):
    help = 'Update file categories'

    def handle(self, *args, **options):
        files_to_update = UploadedFile.objects.all()

        for file in files_to_update:
            file.save()

            self.stdout.write(self.style.SUCCESS(f'File {file} budget updated successfully.'))
