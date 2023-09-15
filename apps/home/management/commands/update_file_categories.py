from django.core.management.base import BaseCommand
from apps.home.models import UploadedFile


class Command(BaseCommand):
    help = 'Update file categories'

    def handle(self, *args, **options):
        files_to_update = UploadedFile.objects.filter(category='others')

        for file in files_to_update:
            current_file_category = file.category
            category = file.fileCategory()
            file.category = category
            file.save()

            self.stdout.write(self.style.SUCCESS(f'File {file.file.name.split("/")[-1]} category updated from '
                                                 f'{current_file_category} to {file.category}.'))
