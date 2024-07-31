import pytz
from datetime import datetime
from celery import shared_task
from core.settings import EMAIL_HOST_USER
from django.core.mail import send_mail
# TODO: Implement email templates


@shared_task(bind=True)
def send_mail_celery(self, subject, message, author, recipient_list, html=None):
    send_mail(subject, message, author, recipient_list, fail_silently=True, html_message=html)
    return 'Done!'


@shared_task(bind=True)
def confirm_register_email(self, path, email, token):
    subject = 'Register confirmation'

    message = (
        f'Hello! Please click the link below to confirm your email.\n\n'
        f'{path}/validate/{token}\n\n'
        f'If you did not request this, please ignore this email.\n\n'
        f'Thanks, Infinite Foundry.'
    )

    email_from = EMAIL_HOST_USER
    to_email = [email]
    send_mail_celery.delay(subject, message, email_from, to_email)


@shared_task(bind=True)
def reset_password_email(self, path, username, token):
    subject = 'Password reset'

    message = (f'Hello! Please click the link below to reset your password.\n\n'
               f'{path}/reset-password/{token}\n\n'
               f'If you did not request this, please ignore this email.\n\n'
               f'Thanks, Infinite Foundry.')

    email_from = EMAIL_HOST_USER
    to_email = [username]
    send_mail_celery.delay(subject, message, email_from, to_email)


@shared_task(bind=True)
def reset_password_confirmation_email(self, username):
    subject = 'Password changed'

    date = datetime.now(tz=pytz.utc).strftime("%d/%m/%Y %H:%M:%S")

    message = (f'Hello! Your password has been changed at {date} UTC.\n\n'
               f'If you did not request this, please contact us.\n\n'
               f'Thanks, Infinite Foundry.')

    email_from = EMAIL_HOST_USER
    to_email = [username]
    send_mail_celery.delay(subject, message, email_from, to_email)
