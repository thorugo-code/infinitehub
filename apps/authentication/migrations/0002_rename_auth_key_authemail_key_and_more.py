# Generated by Django 4.2.11 on 2024-04-25 15:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('authentication', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='authemail',
            old_name='auth_key',
            new_name='key',
        ),
        migrations.RenameField(
            model_name='authemail',
            old_name='auth_token',
            new_name='token',
        ),
        migrations.AlterField(
            model_name='authemail',
            name='user',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='auth_email', to=settings.AUTH_USER_MODEL),
        ),
    ]
