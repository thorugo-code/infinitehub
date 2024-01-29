from django.db.models import Q
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Permission


class Command(BaseCommand):
    help = 'Add permissions to users'

    def handle(self, *args, **options):

        admin_group = [
            'admin@infinitefoundry.com',
            'agodinholuz@infinitefoundry.com',
            'brunoeisinger@infinitefoundry.com',
            'dieynieleandrade@infinitefoundry.com',
            'joaoeisinger@infinitefoundry.com',
        ]

        admin_permissions_list = [
            'add_client',
            'change_client',
            'delete_client',
            'view_client',
            'add_office',
            'change_office',
            'delete_office',
            'view_office',
            'add_bill',
            'change_bill',
            'delete_bill',
            'view_bill',
            'add_document',
            'change_document',
            'delete_document',
            'view_document',
            'change_collaborator',
            'delete_collaborator',
        ]

        collaborators_permissions_list = [
            'view_client',
            'view_office',
        ]

        collaborators_requirement = '@infinitefoundry.com'

        admin_permissions = Permission.objects.filter(Q(codename__in=admin_permissions_list))

        collaborators_permissions = Permission.objects.filter(Q(codename__in=collaborators_permissions_list))

        for user in User.objects.all():
            if user.username in admin_group:
                user.user_permissions.set(admin_permissions)
                self.stdout.write(f'Administrator permissions added to user: {self.style.SUCCESS(user.username)}')
            elif collaborators_requirement in user.username:
                user.user_permissions.set(collaborators_permissions)
                self.stdout.write(f'Collaborator permissions added to user: {self.style.SUCCESS(user.username)}')
            else:
                delete_user = input(f'User seems to be invalid: {self.style.ERROR(user.username)}. Delete it? (y/n): ')
                if delete_user.lower() == 'y':
                    user.delete()
                    self.stdout.write(f'User deleted: {self.style.ERROR(user.username)}')
                else:
                    self.stdout.write(f'User not deleted: {self.style.SUCCESS(user.username)}')
