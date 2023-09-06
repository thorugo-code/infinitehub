
from datetime import datetime
from django.db import models
from django.contrib.auth.models import User


class Project(models.Model):

    title = models.CharField(max_length=100)
    client = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    client_area = models.CharField(max_length=100)
    start_date = models.DateField()
    deadline = models.DateField()
    about = models.TextField()
    img = models.ImageField(upload_to=f'apps/static/assets/uploads/', default='apps/static/assets/img/icons/custom/1x/placeholder.webp')


def custom_upload_path(instance, filename):
    client = instance.project.client.replace(" ", "_")
    project_name = instance.project.title.replace(" ", "_")
    year = datetime.now().strftime('%Y')
    month = datetime.now().strftime('%m')
    return f'uploads/projects/{client}/{project_name}/{year}/{month}/{filename}'


class UploadedFile(models.Model):
    project = models.ForeignKey(Project, related_name='uploaded_files', on_delete=models.CASCADE)
    file = models.FileField(upload_to=custom_upload_path)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.file.name

