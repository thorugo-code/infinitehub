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
    path('projects/working/archive=<int:id>/redirect-to=<str:situation_page>', projects.change_archive,
         name='archive_project'),
    path('projects/archive/unarchive=<int:id>/redirect-to=<str:situation_page>', projects.change_archive,
         name='unarchive_project'),
    path('projects/change-status=<int:project_id>/redirect-to=<str:situation_page>', projects.change_project_status,
         name='change_project_status'),

    path('projects/order', projects.sort_and_filter_projects, name='sort_projects'),
    path('projects/filter', projects.filter_projects, name='filter_projects'),

    path('projects/order:<str:sorted_by>-<str:sort_type>', projects.page_list, name='sorted_projects'),
    path('projects/filters:<str:filters>', projects.page_list, name='filtered_projects'),
    path('projects/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', projects.page_list,
         name='sorted_filtered_projects'),
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

    path('projects/id=<int:project_id>/link', projects.add_link, name='add_link'),

    path('projects/id=<int:project_id>/delete-link=<int:link_id>', projects.delete_link, name='delete_link'),
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

    path('balance/', balance.home, name='balance_page'),

    path('balance/new', balance.new_bill, name='new_bill'),
    path('balance/delete-bill=<int:bill_id>/', balance.delete_bill, name='delete_bill'),
    path('balance/edit-bill=<int:bill_id>/', balance.edit_bill, name='edit_bill'),
    path('balance/change-bill-status=<int:bill_id>', balance.change_status, name='change_bill_status'),

    path('balance/order', balance.sort_and_filter_bills, name='sort_bills'),
    path('balance/filter', balance.filter_bills, name='filter_bills'),

    path('balance/order:<str:sorted_by>-<str:sort_type>', balance.home, name='sorted_bills'),
    path('balance/filters:<str:filters>', balance.home, name='filtered_bills'),
    path('balance/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', balance.home,
         name='sorted_filtered_bills'),

    path('balance/download-bill=<int:bill_id>', balance.download_bill, name='download_proof'),
]

clients_list_urls = [

    path('clients/', clients.home, name='clients_home'),

    path('clients/new', clients.create, name='create_client'),
    path('clients/<slug:slug>/delete', clients.delete, name='delete_client'),

    path('clients/order', clients.sort, name='sort_clients'),
    path('clients/order:<str:sorted_by>-<str:sort_type>', clients.home, name='sorted_clients'),
    path('clients/filter', clients.filter_clients, name='filter_clients'),
    path('clients/filters:<str:filters>', clients.home, name='filtered_clients'),
    path('clients/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', clients.home,
         name='sorted_filtered_clients'),
]

client_page_urls = [

    path('clients/<slug:slug>', clients.details, name='client_details'),
    path('clients/<slug:slug>/edit', clients.details, name='edit_client'),
    path('clients/<slug:slug>/picture', clients.change_picture, name='change_client_picture'),

]

client_balance_urls = [

    path('clients/<slug:slug>/balance', clients.balance_page, name='client_balance'),
    path('clients/<slug:slug>/balance/new', clients.new_bill, name='new_client_bill'),
    path('clients/<slug:slug>/edit=<int:bill_id>/', clients.edit_bill, name='edit_client_bill'),
    path('clients/<slug:slug>/balance/change-status=<int:bill_id>', clients.change_status,
         name='change_client_bill_status'),
    path('clients/<slug:slug>/balance/delete/<int:bill_id>', clients.delete_bill, name='delete_client_bill'),
    path('clients/<slug:slug>/balance/download-bill=<int:bill_id>', clients.download_bill, name='download_client_proof'),

    path('clients/<slug:slug>/balance/order', clients.sort_and_filter_bills, name='sort_client_balance'),
    path('clients/<slug:slug>/balance/filter', clients.filter_bills, name='filter_client_balance'),

    path('clients/<slug:slug>/balance/order:<str:sorted_by>-<str:sort_type>', clients.balance_page,
         name='sorted_client_balance'),
    path('clients/<slug:slug>/balance/filters:<str:filters>', clients.balance_page, name='filtered_client_balance'),
    path('clients/<slug:slug>/balance/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', clients.balance_page,
         name='sorted_filtered_client_balance'),
]

client_documents_urls = [

    path('clients/<slug:slug>/new-doc', clients.new_document, name='new_client_document'),
    path('clients/<slug:slug>/edit-doc=<int:doc_id>', clients.new_document, name='edit_client_document'),
    path('clients/<slug:slug>/delete-doc=<int:document_id>', clients.delete_document, name='delete_client_document'),
    path('clients/<slug:slug>/documents', clients.documents_page, name='client_documents'),
    path('clients/<slug:slug>/documents/download=<int:document_id>', clients.download_document,
         name='download_client_document'),

    path('clients/<slug:slug>/documents/order', clients.sort_and_filter_documents, name='sort_client_documents'),
    path('clients/<slug:slug>/documents/filter', clients.filter_documents, name='filter_client_documents'),

    path('clients/<slug:slug>/documents/order:<str:sorted_by>-<str:sort_type>', clients.documents_page,
         name='sorted_client_documents'),
    path('clients/<slug:slug>/documents/filters:<str:filters>', clients.documents_page, name='filtered_client_documents'),
    path('clients/<slug:slug>/documents/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>',
         clients.documents_page, name='sorted_filtered_client_documents'),

]

collaborators_page_urls = [

    path('collaborators/<slug:slug>', collaborators.details, name='collaborator_details'),

    path('collaborators/new-document=<int:collab_id>', collaborators.newdoc, name='document_new'),

    path('collaborators/download=<int:document_id>', collaborators.download_document,
         name='download_collaborator_document'),

    path('collaborators/<slug:slug>/delete-document=<int:document_id>', collaborators.delete_document,
         name='delete_document'),

    path('collaborators/<slug:slug>/edit-document=<int:document_id>', collaborators.edit_document,
         name='edit_document'),

    path('collaborators/<slug:slug>/filter', collaborators.filter_docs, name='filter_documents'),

    path('collaborators/<slug:slug>/order', collaborators.sort_docs, name='sort_documents'),

    path('collaborators/<slug:slug>/order:<str:sorted_by>-<str:sort_type>', collaborators.details,
         name='sorted_documents'),

    path('collaborators/<slug:slug>/filters:<str:filters>', collaborators.details,
         name='filtered_documents'),

    path('collaborators/<slug:slug>/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', collaborators.details,
         name='sorted_filtered_documents'),
]

collaborators_list_urls = [

    path('collaborators/', collaborators.page_list, name='collaborators_list'),

    path('collaborators/change=<int:collab_id>', collaborators.change_status, name='collaborator_change_status'),

    path('collaborators/order/', collaborators.sort_collaborators, name='sort_collaborators'),

    path('collaborators/filter/', collaborators.filter_collaborators, name='filter_collaborators'),

    path('collaborators/order:<str:sorted_by>-<str:sort_type>', collaborators.page_list, name='sorted_collaborators'),

    path('collaborators/filters:<str:filters>', collaborators.page_list, name='filtered_collaborators'),

    path('collaborators/order:<str:sorted_by>-<str:sort_type>/filters:<str:filters>', collaborators.page_list,
         name='sorted_filtered_collaborators'),

    path('collaborators/fill=<str:slug>', collaborators.fill_collaborator_initial_infos, name='fill_collaborator'),
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

    path('profile/edit', profile.edit, name='edit_profile'),

    path('profile/save', profile.edit, name='send_edit_profile'),

    path('profile/delete-file=<int:file_id>', profile.delete_file, name='delete_file_from_profile'),
]

offices_urls = [

    path('offices/', offices.home, name='offices_home'),

    path('offices/new', offices.create, name='offices_create'),
    path('offices/edit=<int:office_id>', offices.edit, name='offices_edit'),
    path('offices/delete=<int:office_id>', offices.delete, name='offices_delete'),
]

base_urls = [
    path('', login.index, name='home'),
    # Matches any html file
    re_path(r'^.*\.*', login.pages, name='pages'),
]

urlpatterns = [
    *projects_list_urls, *projects_page_urls, *assets_urls, *collaborators_page_urls, *collaborators_list_urls,
    *balance_urls, *inventory_urls, *profile_urls, *clients_list_urls, *offices_urls, *client_page_urls,
    *client_balance_urls, *client_documents_urls, *base_urls
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
