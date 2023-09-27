import datetime
from django import template
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Project, UploadedFile, Profile, Equipments
from django.core.paginator import Paginator
import os


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index',
               'user_profile': Profile.objects.get(user=request.user)}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        user_profile = Profile.objects.get(user=request.user)
        context['user_profile'] = user_profile
    except Profile.DoesNotExist:
        pass

    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


def get_paginated_projects(request):
    projects_list = Project.objects.all()
    paginator = Paginator(projects_list, 6)  # Show 6 projects per page
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    return paginator, projects


def get_paginated_equipments(request):
    equipments_list = Equipments.objects.all()
    paginator = Paginator(equipments_list, 6)  # Show 6 projects per page
    page = request.GET.get('page')
    equipments = paginator.get_page(page)
    return paginator, equipments


def get_paginated_files(request, category=None):
    if category is None:
        files_list = UploadedFile.objects.all()
    elif type(category) == str:
        files_list = UploadedFile.objects.filter(category=category)
    else:
        files_list = UploadedFile.objects.filter(category)

    paginator = Paginator(files_list, 6)  # Show 6 files per page
    page = request.GET.get('page')
    files = paginator.get_page(page)
    return paginator, files


def project_list(request):
    user_profile = Profile.objects.get(user=request.user)
    paginator, projects = get_paginated_projects(request)
    return render(request, "home/projectsList.html", {'projects_list': projects, 'user_profile': user_profile})


def assets_list(request, category=None):
    user_profile = Profile.objects.get(user=request.user)

    if category == '3d-models':
        title = '3D Models'
        paginator, files = get_paginated_files(request, category)
    elif category == 'scripts':
        title = 'Scripts'
        paginator, files = get_paginated_files(request, category)
    elif category == 'unity':
        title = 'Unity'
        paginator, files = get_paginated_files(request, category)
    else:
        title = 'Others'
        category_filter = Q(category__in=['clouds', 'executable', 'folders', 'database',
                                          'office', 'images', 'video', 'others'])
        paginator, files = get_paginated_files(request, category_filter)

    return render(request, "home/assetsList.html", {'files_list': files,
                                                    'category': category,
                                                    'title': title,
                                                    'user_profile': user_profile})


def assets_hub(request):
    user_profile = Profile.objects.get(user=request.user)

    # other_categories = ['3d-models', 'clouds', 'scripts', 'executable', 'folders',
    #               'unity', 'database', 'office', 'images', 'video', 'others']

    other_categories = ['clouds', 'executable', 'folders', 'database', 'office', 'images', 'video', 'others']

    category_filter = Q(category__in=other_categories)

    models_3d = UploadedFile.objects.filter(category='3d-models').count()
    scripts = UploadedFile.objects.filter(category='scripts').count()
    unity = UploadedFile.objects.filter(category='unity').count()
    others = UploadedFile.objects.filter(category_filter).count()

    values_3d = UploadedFile.objects.filter(category='3d-models').aggregate(Sum('value'))['value__sum']
    values_scripts = UploadedFile.objects.filter(category='scripts').aggregate(Sum('value'))['value__sum']
    values_unity = UploadedFile.objects.filter(category='unity').aggregate(Sum('value'))['value__sum']
    values_others = UploadedFile.objects.filter(category_filter).aggregate(Sum('value'))['value__sum']

    return render(request, "home/assetsPage.html", {'3d_models_files': models_3d,
                                                    'scripts_files': scripts,
                                                    'unity_files': unity,
                                                    'others_files': others,
                                                    '3d_models_value': values_3d if values_3d is not None else 0,
                                                    'scripts_value': values_scripts if values_scripts is not None else 0,
                                                    'unity_value': values_unity if values_unity is not None else 0,
                                                    'others_value': values_others if values_others is not None else 0,
                                                    'user_profile': user_profile})


def project(request):
    if request.method == 'POST':

        # Retrieve form data
        title = request.POST['title']
        client = request.POST['client']
        country = request.POST['country']
        client_area = request.POST['client_area']
        start_date = request.POST['start_date']
        deadline = request.POST['deadline']
        about = request.POST['about']

        # Create a new Project instance and save it to the database
        project = Project(
            title=title,
            client=client,
            country=country,
            client_area=client_area,
            start_date=start_date,
            deadline=deadline,
            about=about,
        )

        project.save()
        # Redirect to the newly created project page     
        # return render(request, f'home/project.html', {'project': project, 'id': project.id})
        return redirect('project_details', id=project.id)

    elif request.method == 'GET':

        project_id = request.GET.get('id')

        user_profile = Profile.objects.get(user=request.user)

        request_project = Project.objects.get(id=project_id)

        return render(request, 'home/project.html', {'project': request_project,
                                                     'user_profile': user_profile})

    # Handle GET request or invalid form submission
    return render(request, 'home/page-404.html')


def project_details(request, id):
    # Retrieve the project using the 'id' argument
    project = Project.objects.get(id=id)

    edit_mode = request.GET.get('edit')

    user_profile = Profile.objects.get(user=request.user)

    if edit_mode is not None:
        edit_mode = True
    else:
        edit_mode = False

    if request.method == 'POST':
        project.title = request.POST.get('title', project.title)
        project.client = request.POST.get('client', project.client)
        project.client_area = request.POST.get('client_area', project.client_area)
        project.country = request.POST.get('country', project.country)
        project.start_date = request.POST.get('start_date', project.start_date)
        project.deadline = request.POST.get('deadline', project.deadline)
        project.about = request.POST.get('about', project.about)
        project.save()

        return redirect('project_details', id=project.id)

    return render(request, 'home/project.html', {'project': project,
                                                 'edit_mode': edit_mode,
                                                 'user_profile': user_profile})


def delete_project(request, id):
    project = get_object_or_404(Project, id=id)

    if request.method == 'POST':
        project.delete()
        return redirect('project_list')

    return redirect('project_list')


def edit_project(request, id):
    project = Project.objects.get(id=id)
    if request.method == 'POST':
        return redirect('project_details', id=project.id)


def change_picture(request, id):
    project = Project.objects.get(id=id)

    if request.method == 'POST':
        file = request.FILES['projectPicture']
        project.img = file
        project.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


def change_profile_picture(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        file = request.FILES['profilePicture']
        user_profile.avatar = file
        user_profile.save()

        return redirect('profile')

    return redirect('profile')


def upload_file(request, id):
    project = Project.objects.get(id=id)

    if request.method == 'POST':
        file = request.FILES['file']

        uploaded_file = UploadedFile.objects.create(project=project, file=file)
        uploaded_file.description = request.POST.get('file_description', 'DEFAULT')

        masked_value = request.POST.get('file_value', 'USD 0.00')
        masked_value = masked_value.replace('USD ', '')
        masked_value = masked_value.replace(',', '')

        uploaded_file.value = masked_value if masked_value != '' else 0

        input_category = request.POST.get('file_type')

        if input_category != 'none':
            uploaded_file.category = input_category
        else:
            uploaded_file.category = uploaded_file.fileCategory()

        uploaded_by = request.user
        uploaded_file.uploaded_by = uploaded_by

        uploaded_file.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


@require_POST
def delete_file(request, project_id, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    if os.path.exists(file_path):
        os.remove(file_path)

    uploaded_file.value = 0
    uploaded_file.save()

    uploaded_file.delete()

    return redirect('project_details', id=project_id)


@require_POST
def delete_file_from_storage(request, category, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    if os.path.exists(file_path):
        os.remove(file_path)

    uploaded_file.value = 0
    uploaded_file.save()

    uploaded_file.delete()

    return redirect('assets_list', category=category)


def download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{uploaded_file.file.name.split("/")[-1]}"'
        return response


def profile(request):
    user = request.user
    user_profile = Profile.objects.get(user=user)
    user_files = UploadedFile.objects.filter(uploaded_by=user)
    user_files_count = user_files.count()

    if request.method == 'POST':
        user.first_name = request.POST.get('first_name', user.first_name)
        user.last_name = request.POST.get('last_name', user.last_name)
        user.save()

        # user_profile.phone = request.POST.get('phone', user_profile.phone)

        user_profile.address = request.POST.get('address', user_profile.address)
        user_profile.city = request.POST.get('city', user_profile.city)
        user_profile.state = request.POST.get('state', user_profile.state)
        user_profile.country = request.POST.get('country', user_profile.country)
        user_profile.postal_code = request.POST.get('postal-code', user_profile.postal_code)

        user_profile.about = request.POST.get('about-user', user_profile.about)

        user_profile.save()

        redirect('profile')

    return render(request, 'home/profile.html', {'user_profile': user_profile,
                                                 'user_files': user_files,
                                                 'user_files_number': user_files_count})


def inventory_list(request):
    if request.method == 'POST':
        name = request.POST.get('name', 'Untitled')
        series = request.POST.get('series', 'N/A')
        supplier = request.POST.get('supplier', 'Untitled')
        acquisition_date = request.POST.get('acquisition_date', datetime.datetime.now)
        price = request.POST.get('equipment_value', 'USD 0.00')
        price = price.replace('USD ', '')
        price = price.replace(',', '')
        description = request.POST.get('description', '')

        equipment = Equipments(name=name,
                               series=series,
                               supplier=supplier,
                               acquisition_date=acquisition_date,
                               price=price if price != '' else 0,
                               description=description)

        equipment.save()

        return redirect('inventory_list')

    paginator, equipments = get_paginated_equipments(request)
    user_profile = Profile.objects.get(user=request.user)

    return render(request, 'home/inventory.html', {'user_profile': user_profile,
                                                   'equipment_list': equipments})


def download_qrcode_inventory(request, equipment_id):
    equipment = get_object_or_404(Equipments, pk=equipment_id)
    qrcode_path = equipment.qrcode
    with open(qrcode_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{equipment.qrcode.split("/")[-1]}"'
        return response


def delete_equipment(request, id):
    equipment = get_object_or_404(Equipments, pk=id)
    equipment.delete()

    return redirect('inventory_list')
