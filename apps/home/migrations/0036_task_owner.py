# Generated by Django 4.2.5 on 2023-12-21 16:22

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('home', '0035_remove_document_uploaded_document_uploaded_at_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_tasks', to=settings.AUTH_USER_MODEL),
        ),
    ]
