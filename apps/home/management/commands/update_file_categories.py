from django.core.management.base import BaseCommand
from apps.home.models import UploadedFile


class Command(BaseCommand):
    help = 'Update file categories'

    def handle(self, *args, **options):
        files_to_update = UploadedFile.objects.all()

        for file in files_to_update:
            category = file.fileCategory()  # Implement your categorization logic here
            file.category = category
            file.save()

        self.stdout.write(self.style.SUCCESS('File categories updated successfully.'))
