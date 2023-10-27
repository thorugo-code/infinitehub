from django.core.management.base import BaseCommand
from apps.home.models import Task


class Command(BaseCommand):
    help = 'Update file categories'

    def handle(self, *args, **options):
        tasks_to_update = Task.objects.all()
        projects_to_update = []

        for task in tasks_to_update:
            task.save()
            if task.project not in projects_to_update:
                projects_to_update.append(task.project)
                self.stdout.write(self.style.SUCCESS(f'Project {task.project} updated.'))
