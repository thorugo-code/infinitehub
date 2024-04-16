from django.core.management.base import BaseCommand
from apps.home.models import Project


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for project in Project.objects.all():
            if 'placeholder' in project.img.name:
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} picture was updated')

            if not project.working:
                project.archive = True
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} was archived')

            if project.finished:
                project.working = False
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} was set as not working')
