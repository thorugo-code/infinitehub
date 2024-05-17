from django.urls import path
from .views import *

urlpatterns = [
    path('api/meeting/', receive, name='meeting'),
]
