# Generated by Django 4.2.9 on 2024-01-17 18:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0039_profile_identification'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='expired',
            field=models.BooleanField(default=False),
        ),
    ]