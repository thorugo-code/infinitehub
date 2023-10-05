from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from apps.home.views import views
from apps.home.views import collaborators
from apps.home.views import profile
from apps.home.views import projects
from apps.home.views import inventory

urlpatterns = [
                  path('', views.index, name='home'),

                  # PROJECTS LIST URLS

                  path('projects/create', projects.create_project, name='create_project'),

                  path('projects/id=<int:id>/', projects.details, name='project_details'),

                  path("projects/", projects.page_list, name="project_list"),

                  path("projects/<str:situation>/", projects.page_list, name="project_list"),

                  path('projects/id=<int:id>/delete', projects.delete, name='delete_project'),

                  path('projects/working/archive=<int:id>/redirect-to=<str:situation_page>', projects.archive,
                       name='archive_project'),

                  path('projects/archive/unarchive=<int:id>/redirect-to=<str:situation_page>', projects.unarchive,
                       name='unarchive_project'),

                  # PROJECT PAGE URLS

                  path('projects/id=<int:id>/upload', projects.upload_file, name='upload_file'),

                  path('projects/id=<int:project_id>/delete=<int:file_id>', projects.delete_file, name='delete_file'),

                  path('download_file/<int:file_id>/', projects.download_file, name='download_file'),

                  path('projects/id=<int:id>/change-picture', projects.change_picture, name='change_picture'),

                  # ASSETS URLS

                  path('assets/', views.assets_hub, name='assets_hub'),

                  path('assets/<str:category>/', views.assets_list, name='assets_list'),

                  path('assets/<str:category>/delete=<int:file_id>', views.delete_file_from_storage,
                       name='delete_file_from_storage'),

                  # COLABORATORS URLS

                  path('collaborators/', collaborators.page_list, name='collaborators_list'),

                  path('collaborators/<str:name>', collaborators.details, name='collaborator_details'),

                  # INVENTORY URLS

                  path('inventory/', inventory.inventory_list, name='inventory_list'),

                  path('inventory/new', inventory.inventory_list, name='new_equipment'),

                  path('inventory/id=<int:id>', inventory.inventory_list, name='equipment_details'),

                  path('inventory/delete=<int:id>', inventory.delete_equipment, name='delete_equipment'),

                  path('inventory/download/qrcode=<int:equipment_id>', inventory.download_qrcode_inventory,
                       name='download_file_from_inventory'),

                  # USER URLS

                  path('profile/', profile.details, name='profile'),

                  path('profile/change-picture', profile.change_picture, name='change_profile_picture'),

                  # Matches any html file
                  re_path(r'^.*\.*', views.pages, name='pages'),

              ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
