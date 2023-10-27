from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.home.models import Project, UploadedFile, Profile, Task
from django.core.paginator import Paginator
import os
from datetime import datetime


def archive(request, id, situation_page=None):
    project = Project.objects.get(id=id)
    project.working = False
    project.save()

    if situation_page is None or situation_page == 'None':
        return redirect('project_list')
    else:
        return redirect('project_list', situation=situation_page)


def unarchive(request, id, situation_page=None):
    project = Project.objects.get(id=id)
    project.working = True
    project.save()

    if situation_page is None or situation_page == 'None':
        return redirect('project_list')
    else:
        return redirect('project_list', situation=situation_page)


def get_paginated_projects(request, situation=None):
    if situation == 'working':
        projects_list = Project.objects.filter(working=True)
    elif situation == 'archive':
        projects_list = Project.objects.filter(working=False)
    else:
        projects_list = Project.objects.all()

    paginator = Paginator(projects_list, 6)
    page = request.GET.get('page')
    projects = paginator.get_page(page)
    return paginator, projects


def page_list(request, situation=None):
    user_profile = Profile.objects.get(user=request.user)
    if situation is not None:
        paginator, projects = get_paginated_projects(request, situation=situation)
    else:
        paginator, projects = get_paginated_projects(request)

    context = {
        'projects_list': projects,
        'user_profile': user_profile,
        'situation': situation
    }

    return render(request, "home/projectsList.html", context)


def create_project(request):
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

        return redirect('project_details', id=project.id)

    elif request.method == 'GET':

        project_id = request.GET.get('id')

        user_profile = Profile.objects.get(user=request.user)

        request_project = Project.objects.get(id=project_id)

        return render(request, 'home/project.html', {'project': request_project,
                                                     'user_profile': user_profile})

    # Handle GET request or invalid form submission
    return render(request, 'home/page-404.html')


def details(request, id):
    project = Project.objects.get(id=id)

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

    user_profile = Profile.objects.get(user=request.user)
    tasks = Task.objects.filter(project=project)

    edit_mode = request.GET.get('edit')

    if edit_mode is not None:
        edit_mode = True
    else:
        edit_mode = False

    context = {
        'project': project,
        'user_profile': user_profile,
        'tasks': tasks,
        'edit_mode': edit_mode
    }

    return render(request, 'home/project.html', context)


def delete(request, id):
    project = get_object_or_404(Project, id=id)

    if request.method == 'POST':
        project.delete()
        return redirect('project_list')

    return redirect('project_list')


def edit(request, id):
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


def change_project_status(request, project_id, situation_page=None):
    project = Project.objects.get(id=project_id)

    if project.finished:
        project.finished = False
    else:
        project.finished = True

    project.save()

    if situation_page is None or situation_page == 'None':
        return redirect('project_list')
    else:
        return redirect('project_list', situation=situation_page)


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


def download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{uploaded_file.file.name.split("/")[-1]}"'
        return response


def submit_task(request, project_id):
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        task = Task(
            project=project,
            title=request.POST.get('taskTitle'),
            description=request.POST.get('taskDescription'),
            deadline=request.POST.get('taskDeadline'),
            priority=int(request.POST.get('taskPriority')),
            created_by=request.user
        )

        task.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


def delete_task(request, project_id, task_id):
    project = Project.objects.get(id=project_id)
    task = Task.objects.get(id=task_id, project=project)
    task.delete()

    return redirect('project_details', id=project_id)


def edit_task(request, project_id, task_id):
    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        task.title = request.POST.get('taskTitleEdit', task.title)
        task.description = request.POST.get('taskDescriptionEdit', task.description)
        task.deadline = request.POST.get('taskDeadlineEdit', task.deadline)
        task.priority = int(request.POST.get('taskPriorityEdit', task.priority))
        task.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


def change_task_status(request, project_id, task_id):
    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        if task.completed:
            task.completed = False
            task.completed_by = None
            task.completed_at = None
        else:
            task.completed = True
            task.completed_by = request.user
            task.completed_at = datetime.now()

        task.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)
