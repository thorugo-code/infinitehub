from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from core.settings import EMAIL_HOST_USER, DEBUG, TEMPLATE_DIR
from apps.tasks import send_mail_celery
from decouple import config


class Command(BaseCommand):
    help = 'Send  message for users.'

    def handle(self, *args, **options):
        if DEBUG:
            users = User.objects.filter(username__in=config('STAFF_USERS', 'admin').split(','))
            subject = 'Manutenção / Maintenance (TEST)'

        else:
            users = User.objects.filter(is_active=True)
            subject = 'Manutenção / Maintenance'

        from_email = EMAIL_HOST_USER

        for user in users:
            topics = config('MAINTENANCE_TOPICS', 'Sua mensagem de aviso sobre manutenção').split(';')
            topics_eng = config('ENG_MAINTENANCE_TOPICS', 'Your maintenance notice').split(';')

            html_message = render_to_string(
                f'{TEMPLATE_DIR}/mail/maintenance.html',
                {'user': user, 'topics': topics, 'topics_eng': topics_eng}
            )

            send_mail_celery.delay(
                subject=subject,
                message='',
                author=from_email,
                recipient_list=[user.email],
                html=html_message
            )

            self.stdout.write(f"Successfully sent maintenance message to {self.style.SUCCESS(user.username)}.")
