# Generated by Django 4.2.14 on 2024-07-29 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0093_rename_location_office_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='office',
            name='duns',
            field=models.CharField(default='', max_length=9),
        ),
        migrations.AddField(
            model_name='office',
            name='municipal_inscription',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AddField(
            model_name='office',
            name='state_inscription',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='office',
            name='address',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='office',
            name='cnpj',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AlterField(
            model_name='office',
            name='name',
            field=models.CharField(default='', max_length=100),
        ),
    ]
