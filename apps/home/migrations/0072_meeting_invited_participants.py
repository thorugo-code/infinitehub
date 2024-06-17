# Generated by Django 4.2.11 on 2024-05-22 16:19

from django.db import migrations
import picklefield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0071_alter_task_deadline_alter_task_project_meeting_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='meeting',
            name='invited_participants',
            field=picklefield.fields.PickledObjectField(default=list, editable=False),
        ),
    ]