from django.db import models
from django.contrib.auth.models import User


class AuthEmail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    auth_token = models.CharField(max_length=100, unique=True)
    auth_key = models.CharField(max_length=44, unique=True)

    is_confirmed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.user.username


class PasswordReset(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    token = models.CharField(max_length=100, unique=True)
    key = models.CharField(max_length=44, unique=True)

    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return self.user.username
