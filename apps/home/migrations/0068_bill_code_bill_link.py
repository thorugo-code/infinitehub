# Generated by Django 4.2.11 on 2024-04-17 14:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0067_project_archive_alter_client_avatar'),
    ]

    operations = [
        migrations.AddField(
            model_name='bill',
            name='code',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='bill',
            name='link',
            field=models.URLField(blank=True, null=True),
        ),
    ]
