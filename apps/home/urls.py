# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from apps.home import views
from .views import *

urlpatterns = [

    path('', views.index, name='home'),

    # PROJECTS LIST URLS
    
    path('projects/create', views.project, name='create_project'),
    
    path('projects/id=<int:id>', views.project_details, name='project_details'),
    
    path("projects/", project_list, name="project_list"),

    path('projects/id=<int:id>/delete', views.delete_project, name='delete_project'),

    # PROJECT PAGE URLS

    path('projects/id=<int:id>/upload', views.upload_file, name='upload_file'),

    path('projects/id=<int:project_id>/delete=<int:file_id>', views.delete_file, name='delete_file'),

    path('download_file/<int:file_id>/', views.download_file, name='download_file'),
    
    path('projects/id=<int:id>/change-picture', views.change_picture, name='change_picture'),

    # ASSETS URLS

    path('assets/', views.assets_hub, name='assets_hub'),

    path('assets/<str:category>/', views.assets_list, name='assets_list'),

    path('assets/<str:category>/delete=<int:file_id>', views.delete_file_from_storage, name='delete_file_from_storage'),

    # INVENTORY URLS

    path('inventory/', views.inventory_list, name='inventory_list'),

    path('inventory/new', views.inventory_list, name='new_equipment'),

    path('inventory/delete=<int:id>', views.delete_equipment, name='delete_equipment'),

    path('inventory/id=<int:id>', views.inventory_list, name='equipment_details'),

    path('inventory/download/qrcode=<int:equipment_id>', views.download_qrcode_inventory, name='download_file_from_inventory'),

    # USER URLS

    path('profile/', views.profile, name='profile'),

    path('profile/change-picture', views.change_profile_picture, name='change_profile_picture'),

    # Matches any html file
    re_path(r'^.*\.*', views.pages, name='pages'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
