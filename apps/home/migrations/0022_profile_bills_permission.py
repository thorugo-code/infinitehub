# Generated by Django 4.2.5 on 2023-12-12 18:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0021_bill_remove_billtoreceive_client_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='bills_permission',
            field=models.BooleanField(blank=True, null=True),
        ),
    ]