from django.core.management.base import BaseCommand
from apps.home.models import Equipments


class Command(BaseCommand):
    help = 'Create QRCode for existing equipments'

    def handle(self, *args, **options):
        equipments = Equipments.objects.all()

        for equipment in equipments:
            print(f'Updating {equipment.name}...')
            equipment.save()

        self.stdout.write(self.style.SUCCESS('Successfully updated all equipments'))

