# Generated by Django 4.2.5 on 2023-11-16 17:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0012_rename_sub_category_billtopay_subcategory_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='billtoreceive',
            name='subcategory',
        ),
    ]