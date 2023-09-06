# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from django import template
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Project, UploadedFile
from django.core.paginator import Paginator
import os


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index'}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
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


def get_paginated_files(request):
    files_list = UploadedFile.objects.all()
    paginator = Paginator(files_list, 6)  # Show 6 files per page
    page = request.GET.get('page')
    files = paginator.get_page(page)
    return paginator, files


def project_list(request):
    paginator, projects = get_paginated_projects(request)
    return render(request, "home/projectsList.html", {'projects_list': projects})


def assets_list(request, category):
    paginator, files = get_paginated_files(request)
    if category == '3d-models':
        title = '3D Models'
    elif category == 'scripts':
        title = 'Scripts'
    elif category == 'unity':
        title = 'Unity'
    else:
        title = 'Others'

    return render(request, "home/assetsList.html", {'files_list': files, 'title': title})


def assets_hub(request):
    return render(request, "home/assetsPage.html")


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
        
        request_project = Project.objects.get(id=project_id)
        
        return render(request, 'home/project.html', {'project': request_project})

    # Handle GET request or invalid form submission
    return render(request, 'home/page-404.html')


def project_details(request, id):
    # Retrieve the project using the 'id' argument
    project = Project.objects.get(id=id)

    edit_mode = request.GET.get('edit')

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
    
    return render(request, 'home/project.html', {'project': project, 'edit_mode': edit_mode})


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


def upload_file(request, id):
    project = Project.objects.get(id=id)

    if request.method == 'POST':
        file = request.FILES['file']
        uploaded_file = UploadedFile.objects.create(project=project, file=file)

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


@require_POST
def delete_file(request, project_id, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    if os.path.exists(file_path):
        os.remove(file_path)
    uploaded_file.delete()

    return redirect('project_details', id=project_id)


def download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{uploaded_file.file.name.split("/")[-1]}"'
        return response


def profile(request):
    user = request.user
    edit_mode = request.GET.get('edit')
    if edit_mode is not None:
        edit_mode = True
    else:
        edit_mode = False

    if request.method == 'POST':
        user.first_name = request.POST.get('input-first-name', user.first_name)
        user.last_name = request.POST.get('input-last-name', user.last_name)
        user.email = request.POST.get('input-email', user.email)

        user.save()

        return redirect('profile')

    return render(request, 'home/profile.html', {'edit_mode': edit_mode})
