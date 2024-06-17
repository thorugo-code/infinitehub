from django.contrib import admin
from .models import AuthEmail, PasswordReset


admin.site.register(AuthEmail)
admin.site.register(PasswordReset)

