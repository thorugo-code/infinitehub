from django.core.management.base import BaseCommand
from apps.home.models import Project, Client


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        correlation = {
            'infinite foundry': None,
            'infinitefoundry': None,
            'shinagawa': 1,
            'embraer': 4,
            'mercedes': 7,
            'renault': 3,
            'intelbras': None,
            'samarco': None,
            '3m': None,
            'novo nordisk': 9,
            'arcelormittal t': 2,
            'sc braga': None,
            'rhi magnesita': 10,
            'ogma': None,
            'aquinos': None,
            'saint-gobain': None,
            'huawei': None,
            'lanxess': None,
        }

        for project in Project.objects.all():
            client = project.client
            if client is None:
                for corr_key, client_id in zip(correlation.keys(), correlation.values()):
                    if corr_key in project.client_str.lower() and client_id:
                        client = Client.objects.get(id=client_id) if client_id else None
                        project.client = client
                        project.save()
                        self.stdout.write(f'Project with previous client "{project.client_str}" '
                                          f'changed client object to {self.style.SUCCESS(client.name)}.')
                        break

