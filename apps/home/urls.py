from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path
from apps.home.views import assets, collaborators, inventory, login, profile, projects, balance, clients, offices

projects_list_urls = [

    path('projects/create', projects.create_project, name='create_project'),

    path('projects/id=<int:id>/', projects.details, name='project_details'),

    path("projects/", projects.page_list, name="project_list"),

    path("projects/<str:situation>/", projects.page_list, name="project_list"),

    path('projects/id=<int:id>/delete', projects.delete, name='delete_project'),

    path('projects/working/archive=<int:id>/redirect-to=<str:situation_page>', projects.archive,
         name='archive_project'),

    path('projects/archive/unarchive=<int:id>/redirect-to=<str:situation_page>', projects.unarchive,
         name='unarchive_project'),

    path('projects/change-status=<int:project_id>/redirect-to=<str:situation_page>', projects.change_project_status,
         name='change_project_status'),
]

projects_page_urls = [

    path('projects/id=<int:id>/upload', projects.upload_file, name='upload_file'),

    path('projects/id=<int:project_id>/delete=<int:file_id>', projects.delete_file, name='delete_file'),

    path('download_file/<int:file_id>/', projects.download_file, name='download_file'),

    path('projects/id=<int:id>/change-picture', projects.change_picture, name='change_picture'),

    path('projects/id=<int:project_id>/submit-task', projects.submit_task, name='submit_task'),

    path('projects/id=<int:project_id>/task=<int:task_id>/change-status', projects.change_task_status,
         name='change_task_status'),

    path('projects/id=<int:project_id>/edit=<int:task_id>/', projects.edit_task, name='edit_task'),

    path('projects/id=<int:project_id>/delete-task=<int:task_id>', projects.delete_task, name='delete_task'),
]

assets_urls = [

    path('assets/', assets.assets_hub, name='assets_hub'),

    path('assets/<str:category>/', assets.assets_list, name='assets_list'),

    path('assets/<str:category>/delete=<int:file_id>', assets.delete_file_from_storage_with_category,
         name='delete_file_from_storage_with_category'),

    path('assets/delete=<int:file_id>', assets.delete_file_from_storage,
         name='delete_file_from_storage'),
]

balance_urls = [

    # path('balance/', balance.home, name='balance_page'),
    path('balance/', balance.home, name='balance_page'),

    path('balance/new', balance.new_bill, name='new_bill'),
    path('balance/delete-bill=<int:bill_id>/', balance.delete_bill, name='delete_bill'),
    path('balance/change-bill-status=<int:bill_id>', balance.change_status, name='change_bill_status'),

    path('balance/order', balance.sort_bills, name='sort_bills'),
    path('balance/order:<str:sorted_by>-<str:sort_type>', balance.home, name='sorted_bills'),

    path('balance/filter', balance.filter_bills, name='filter_bills'),
    path('balance/filters:<str:filters>', balance.home, name='filtered_bills'),

    path('balance/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', balance.home,
         name='sorted_filtered_bills'),
]

clients_urls = [

    path('clients/', clients.home, name='clients_home'),
    path('clients/new', clients.create, name='create_client'),
    path('clients/delete=<int:client_id>', clients.delete, name='delete_client'),
]

collaborators_urls = [

    path('collaborators/', collaborators.page_list, name='collaborators_list'),

    path('collaborators/<str:collab_name>-<int:collab_id>', collaborators.details, name='collaborator_details'),

    path('collaborators/new', collaborators.new, name='collaborator_new'),

    path('collaborators/change=<int:collab_id>', collaborators.change_status, name='collaborator_change_status'),
]

inventory_urls = [

    path('inventory/', inventory.inventory_list, name='inventory_list'),

    path('inventory/new', inventory.inventory_list, name='new_equipment'),

    path('inventory/id=<int:id>', inventory.inventory_list, name='equipment_details'),

    path('inventory/delete=<int:id>', inventory.delete_equipment, name='delete_equipment'),

    path('inventory/download/qrcode=<int:equipment_id>', inventory.download_qrcode_inventory,
         name='download_file_from_inventory'),
]

profile_urls = [

    path('profile/', profile.details, name='profile'),

    path('profile/change-picture', profile.change_picture, name='change_profile_picture'),
]

offices_urls = [

    path('offices/', offices.home, name='offices_home'),
    path('offices/new', offices.create, name='offices_create'),
    path('offices/delete=<int:office_id>', offices.delete, name='offices_delete'),
]

base_urls = [

    path('', login.index, name='home'),
    # Matches any html file
    re_path(r'^.*\.*', login.pages, name='pages'),

]

urlpatterns = projects_list_urls + projects_page_urls + assets_urls + collaborators_urls + inventory_urls + profile_urls
urlpatterns += balance_urls + clients_urls + offices_urls + base_urls

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
