from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from apps.authentication.models import AuthEmail
import django.db.utils
from cryptography.fernet import Fernet


class Command(BaseCommand):
    help = 'Init database with custom commands'

    def handle(self, *args, **options):

        for user in User.objects.all():
            if not user.is_superuser:
                user.is_active = False
                user.save()

            auth_email, created = AuthEmail.objects.get_or_create(user=user)

            if created:
                auth_email.is_confirmed = False
                key = Fernet.generate_key()
                cipher_suite = Fernet(key)
                token = cipher_suite.encrypt(user.username.encode())
                auth_email.auth_token = token.decode()
                auth_email.auth_key = key.decode()
                auth_email.save()

            self.stdout.write(self.style.SUCCESS(f'User {user.username} has been initialized.'))
