# Generated by Django 4.2.5 on 2023-12-19 13:45

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('home', '0030_merge_20231219_1016'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='UploadedDocument',
            new_name='Document',
        ),
        migrations.RenameField(
            model_name='profile',
            old_name='first_login',
            new_name='first_access',
        ),
        migrations.AddField(
            model_name='profile',
            name='active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='admission',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='birthday',
            field=models.DateField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name='profile',
            name='contract',
            field=models.CharField(default='', max_length=100),
        ),
        migrations.AddField(
            model_name='profile',
            name='phone',
            field=models.CharField(default='', max_length=20),
        ),
        migrations.AlterField(
            model_name='document',
            name='collab',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='document', to='home.profile'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='office',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='collaborators', to='home.office'),
        ),
        migrations.DeleteModel(
            name='Collaborator',
        ),
    ]
