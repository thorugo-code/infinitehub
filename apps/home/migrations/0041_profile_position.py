# Generated by Django 4.2.9 on 2024-01-22 17:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0040_document_expired'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='position',
            field=models.CharField(default='', max_length=100),
        ),
    ]
