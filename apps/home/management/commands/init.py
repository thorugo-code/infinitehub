from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session
from apps.home.models import Project, Office, Bill, BillProof


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        # Delete all sessions
        self.stdout.write(f'Deleting sessions...', ending=' ')
        for session in Session.objects.all():
            session.delete()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))

        # Update Projects
        self.stdout.write(f'Updating projects...', ending=' ')
        for project in Project.objects.all():
            project.save()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))

        # Update Offices
        self.stdout.write(f'Updating offices...', ending=' ')
        for office in Office.objects.all():
            office.save()
        else:
            self.stdout.write(self.style.SUCCESS('OK'))

        # Update Bill Proofs
        bills = Bill.objects.exclude(proof='')
        for bill in bills:
            self.stdout.write(f'Migrating proof for Bill: {bill.title}...')

            bill_proof = BillProof.objects.create(
                bill=bill,
                file=bill.proof,
            )

            bill_proof.save()

            bill.proof = None
            bill.save()

            self.stdout.write(f'Proof for Bill: {bill.title} migrated successfully')

        self.stdout.write('Migration completed successfully')
