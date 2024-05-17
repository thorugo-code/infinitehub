from django.db import models
from django.contrib.auth.models import User


class Meeting(models.Model):
    participants = models.ManyToManyField(User, related_name='meetings')
