# Generated by Django 4.2.5 on 2023-12-19 17:02

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0033_alter_document_collab'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='collab',
        ),
        migrations.AddField(
            model_name='document',
            name='user',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL),
        ),
    ]
