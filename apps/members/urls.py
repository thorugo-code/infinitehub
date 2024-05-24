from django.urls import path
from .views import *

urlpatterns = [
    path('members/<str:identifier>', detail, name='member_detail'),
]
