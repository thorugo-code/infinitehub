# Generated by Django 4.2.11 on 2024-05-27 13:07

import apps.home.storage_backends
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0075_profile_qrcode'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='qrcode',
            field=models.ImageField(blank=True, null=True, storage=apps.home.storage_backends.PublicMediaStorage(), upload_to='qrcodes/members/'),
        ),
    ]
