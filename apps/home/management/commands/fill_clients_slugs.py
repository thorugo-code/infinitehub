from django.core.management.base import BaseCommand
from apps.home.models import Client


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for client in Client.objects.all():
            if client.slug:
                continue
            else:
                client.save()
                self.stdout.write(
                    f'Client {self.style.SUCCESS(client.name)} slug updated.')
