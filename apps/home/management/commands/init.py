from django.core.management.base import BaseCommand
from apps.home.models import Project, Client
from apps.authentication.models import AuthEmail
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        # Update clients slugs
        for client in Client.objects.all():
            if client.slug:
                continue
            else:
                client.save()
                self.stdout.write(
                    f'Client {self.style.SUCCESS(client.name)} slug updated.')

        # Update projects pictures, archive and working status
        for project in Project.objects.all():
            if 'placeholder' in project.img.name:
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} picture was updated')

            if not project.working and not project.archive and not project.finished:
                project.archive = True
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} was archived')

            if project.finished and project.working:
                project.working = False
                project.save()
                self.stdout.write(f'Project {self.style.SUCCESS(project.title)} was set as not working')

        # Delete unconfirmed AuthEmails
        for auth in AuthEmail.objects.all():
            if not auth.is_confirmed:
                auth.delete()
                self.stdout.write(f'AuthEmail {self.style.SUCCESS(auth)} was deleted')

        # Set unconfirmed users as not active
        for user in User.objects.all():
            try:
                _ = AuthEmail.objects.get(user=user)
                continue
            except AuthEmail.DoesNotExist:
                user.is_active = False
                user.save()
                self.stdout.write(f'User {self.style.SUCCESS(user.username)} was set as not active')
