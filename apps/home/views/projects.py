from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.views.decorators.http import require_POST
from apps.home.models import Project, UploadedFile, Profile, Task, Client, Link
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from datetime import datetime
from django.db.models import Q
from django.core.files.storage import default_storage
from django.urls import reverse
from urllib.parse import urlencode


def change_archive(request, id, situation_page=None):
    project = Project.objects.get(id=id)
    if not project.archive and not project.finished or project.working:
        project.working = False
    elif not project.finished:
        project.working = True

    project.archive = not project.archive
    project.save()

    sorted_by = request.POST.get('sort_by', '')
    sort_type = request.POST.get('sort_type', 'desc')
    filters = request.POST.get('filters', 'None')
    page = request.POST.get('page', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_filtered_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type, 'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_filtered_projects', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by not in ['', 'None']:
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_projects', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('filtered_projects',
                          kwargs={'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('filtered_projects', filters=filters)
    else:
        if situation_page is None or situation_page == 'None':
            if page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('project_list') + '?' + query_params
                return redirect(url)
            else:
                return redirect('project_list')
        elif page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('project_list', kwargs={'situation': situation_page}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('project_list', situation=situation_page)


def change_project_status(request, project_id, situation_page=None):
    project = Project.objects.get(id=project_id)
    if not project.archive and not project.finished or project.working:
        project.working = False
    elif not project.archive:
        project.working = True

    project.finished = not project.finished
    project.save()

    sorted_by = request.POST.get('sort_by', '')
    sort_type = request.POST.get('sort_type', 'desc')
    filters = request.POST.get('filters', 'None')
    page = request.POST.get('page', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_filtered_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type, 'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_filtered_projects', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by not in ['', 'None']:
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_projects', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('filtered_projects',
                          kwargs={'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('filtered_projects', filters=filters)
    else:
        if situation_page is None or situation_page == 'None':
            if page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('project_list') + '?' + query_params
                return redirect(url)
            else:
                return redirect('project_list')
        elif page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('project_list', kwargs={'situation': situation_page}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('project_list', situation=situation_page)


def get_paginated_projects(request, projects=None, situation=None, sorted_by=None, sort_type=None, page=None):
    if projects is None:
        projects_list = Project.objects.all()
    else:
        projects_list = projects

    if situation == 'working':
        projects_list = projects_list.filter(working=True)
    elif situation == 'archive':
        projects_list = Project.objects.all().filter(archive=True)
    elif situation == 'finished':
        projects_list = projects_list.filter(finished=True)

    if sorted_by is not None and sorted_by == 'client':
        projects_list = projects_list.order_by(f'{"-" if sort_type == "desc" else ""}client__name')
    elif sorted_by is not None and sorted_by == 'performance':
        projects_list = projects_list.order_by(f'{"-" if sort_type == "desc" else ""}completition')
    elif sorted_by is not None:
        projects_list = projects_list.order_by(f'{"-" if sort_type == "desc" else ""}{sorted_by}')

    paginator = Paginator(projects_list, 6)
    if page is None or page == 'None':
        page = request.GET.get('page')

    projects = paginator.get_page(page)
    return paginator, projects


def page_list(request, situation=None, filters=None, sorted_by=None, sort_type=None, page=None):
    user_profile = Profile.objects.get(user=request.user)
    projects = filter_project_objects(filters)

    if situation is not None:
        paginator, projects = get_paginated_projects(request, projects, situation=situation,
                                                     sorted_by=sorted_by, sort_type=sort_type, page=page)
    else:
        paginator, projects = get_paginated_projects(request, projects,
                                                     sorted_by=sorted_by, sort_type=sort_type, page=page)

    context = {
        'projects_list': projects,
        'user_profile': user_profile,
        'situation': situation,
        'clients': sorted(Client.objects.all(), key=lambda x: x.name),
        'collaborators': Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(
            user__username__startswith='admin@'),
        'segment': 'projects',
        'sorted_by': sorted_by,
        'sort_type': sort_type,
        'filters': filters,
    }

    return render(request, "home/projectsList.html", context)


def create_project(request):
    if request.method == 'POST':

        # Retrieve form data
        title = request.POST['title']
        client = Client.objects.get(id=request.POST['client']) if request.POST.get('client') else None
        country = request.POST['country']
        start_date = request.POST['start_date']
        deadline = request.POST['deadline']
        about = request.POST['about']

        # Create a new Project instance and save it to the database
        project = Project(
            title=title,
            client=client,
            country=country,
            start_date=start_date,
            deadline=deadline,
            about=about,
        )

        project.save()

        for collaborator_id in request.POST.getlist("collaborators-choice"):
            project.assigned_to.add(User.objects.get(id=Profile.objects.get(id=collaborator_id).user.id))

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


def delete(request, id, situation_page=None):
    project = get_object_or_404(Project, id=id)

    if request.method == 'POST':
        if 'placeholder' not in project.img.name:
            if project.client and project.client.avatar != project.img:
                project.img.delete(save=False)

        project.delete()

        sorted_by = request.POST.get('sort_by', '')
        sort_type = request.POST.get('sort_type', 'desc')
        filters = request.POST.get('filters', 'None')
        page = request.POST.get('page', 'None')

        if sorted_by not in ['', 'None'] and filters != 'None':
            if page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('sorted_filtered_projects',
                              kwargs={'sorted_by': sorted_by, 'sort_type': sort_type, 'filters': filters}) + '?' + query_params
                return redirect(url)
            else:
                return redirect('sorted_filtered_projects', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
        elif sorted_by not in ['', 'None']:
            if page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('sorted_projects',
                              kwargs={'sorted_by': sorted_by, 'sort_type': sort_type}) + '?' + query_params
                return redirect(url)
            else:
                return redirect('sorted_projects', sorted_by=sorted_by, sort_type=sort_type)
        elif filters != 'None':
            if page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('filtered_projects',
                              kwargs={'filters': filters}) + '?' + query_params
                return redirect(url)
            else:
                return redirect('filtered_projects', filters=filters)
        else:
            if situation_page is None or situation_page == 'None':
                if page != 'None':
                    query_params = urlencode({'page': page})
                    url = reverse('project_list') + '?' + query_params
                    return redirect(url)
                else:
                    return redirect('project_list')
            elif page != 'None':
                query_params = urlencode({'page': page})
                url = reverse('project_list', kwargs={'situation': situation_page}) + '?' + query_params
                return redirect(url)
            else:
                return redirect('project_list', situation=situation_page)

    return redirect('project_list')


def sort_and_filter_projects(request):
    sorted_by = request.POST.get('sort_by', '')
    sort_type = 'asc' if request.POST.get('asc') else 'desc'
    filters = request.POST.get('filters', 'None')
    page = request.POST.get('page', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_filtered_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type, 'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_filtered_projects', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by not in ['', 'None']:
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_projects', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('filtered_projects',
                          kwargs={'filters': filters}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('filtered_projects', filters=filters)
    elif page != 'None':
        query_params = urlencode({'page': page})
        url = reverse('project_list') + '?' + query_params
        return redirect(url)
    else:
        return redirect('project_list')


def filter_project_objects(filters):
    projects = Project.objects.all()
    if filters is not None:
        filters_list = filters.split('&')

        client, country, schedule = 'all', 'all', 'all'
        from_date, to_date = False, False
        archive, working, finished = True, True, True
        collaborators = None

        for item in filters_list:
            from_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('from') else from_date
            to_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            client = item.split('=')[1] if item.startswith('client') else client
            country = item.split('=')[1] if item.startswith('country') else country
            schedule = item.split('=')[1] if item.startswith('schedule') else schedule
            collaborators = item.split('=')[1] if item.startswith('collaborators') else collaborators
            archive = item.split('=')[1] if item.startswith('archive') else archive
            working = item.split('=')[1] if item.startswith('working') else working
            finished = item.split('=')[1] if item.startswith('finished') else finished

        if archive == 'on' and working == 'off' and finished == 'off':
            filtered_projects = projects.filter(archive=True)
        elif archive == 'on' and working == 'off':
            filtered_projects = projects.filter(working=False)
        elif archive == 'on' and finished == 'off':
            filtered_projects = projects.filter(Q(archive=True) | Q(working=True))
        elif working == 'off':
            filtered_projects = projects.filter(working=False, archive=False)
        elif finished == 'off':
            filtered_projects = projects.filter(finished=False, archive=False)
        elif archive == 'on':
            filtered_projects = projects
        else:
            filtered_projects = projects.filter(archive=False)

        if from_date and to_date:
            filtered_projects = filtered_projects.filter(deadline__gte=from_date, deadline__lte=to_date)
        elif from_date:
            filtered_projects = filtered_projects.filter(deadline__gte=from_date)
        elif to_date:
            filtered_projects = filtered_projects.filter(deadline__lte=to_date)

        if client != 'all':
            filtered_projects = filtered_projects.filter(client=Client.objects.get(id=client))

        if country != 'all':
            filtered_projects = filtered_projects.filter(country=country)

        if schedule != 'all':
            if schedule == 'late':
                filtered_projects = filtered_projects.filter(deadline__lt=datetime.now(), finished=False)
            elif schedule == 'ontime':
                filtered_projects = filtered_projects.filter(deadline__gte=datetime.now())

        if collaborators is not None:
            collaborators = collaborators.split('-')
            query = Q()
            for collaborator_id in collaborators:
                collaborator_user = User.objects.get(id=collaborator_id)
                query |= Q(assigned_to=collaborator_user)

            filtered_projects = filtered_projects.filter(query).distinct().order_by('id')

    else:
        filtered_projects = projects.filter(archive=False)

    return filtered_projects


def filter_projects(request):
    from_date = request.POST['from']
    to_date = request.POST['to']
    client = request.POST['client']
    country = request.POST['country']
    schedule = request.POST['schedule']
    collaborators = request.POST.getlist('collaborators-choice')
    archived = request.POST.get('archived_filter', False)
    working = request.POST.get('working_filter', False)
    finished = request.POST.get('finished_filter', False)

    filter_list = [
        f'from={from_date}' if from_date != '' and from_date != to_date else '%',
        f'to={to_date}' if to_date != '' and from_date != to_date else '%',
        f'client={client}' if client != 'all' else '%',
        f'schedule={schedule}' if schedule != 'all' else '%',
        f'country={country}' if country != 'all' else '%',
        f'collaborators={"-".join(collaborators)}' if collaborators else '%'
    ]

    if not working and not finished and not archived:
        pass
    else:
        filter_list += [
            f'archive={archived}' if archived else '%',
            f'working=off' if not working else '%',
            f'finished=off' if not finished else '%',
        ]

    # Convert the list to a string with appropriate format, avoiding empty values
    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    sorted_by = request.POST.get('sort_by', '')
    sort_type = request.POST.get('sort_type', 'desc')
    page = request.POST.get('page', 'None')

    if sorted_by not in ['', 'None'] and filter_string != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_filtered_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type, 'filters': filter_string}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_filtered_projects', sorted_by=sorted_by, sort_type=sort_type, filters=filter_string)
    elif sorted_by not in ['', 'None']:
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('sorted_projects',
                          kwargs={'sorted_by': sorted_by, 'sort_type': sort_type}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('sorted_projects', sorted_by=sorted_by, sort_type=sort_type)
    elif filter_string != 'None':
        if page != 'None':
            query_params = urlencode({'page': page})
            url = reverse('filtered_projects',
                          kwargs={'filters': filter_string}) + '?' + query_params
            return redirect(url)
        else:
            return redirect('filtered_projects', filters=filter_string)
    elif page != 'None':
        query_params = urlencode({'page': page})
        url = reverse('project_list') + '?' + query_params
        return redirect(url)
    else:
        return redirect('project_list')


#####################################################


def details(request, id):
    project = Project.objects.get(id=id)

    if request.method == 'POST':
        project.title = request.POST.get('title', project.title)
        project.client = Client.objects.get(id=request.POST['client']) if request.POST.get('client') else None
        project.country = request.POST.get('country', project.country)
        project.start_date = request.POST.get('start_date', project.start_date)
        project.deadline = request.POST.get('deadline', project.deadline)
        project.about = request.POST.get('about', project.about)
        project.assigned_to.clear()
        for collaborator_id in request.POST.getlist("collaborators-choice"):
            project.assigned_to.add(User.objects.get(id=Profile.objects.get(id=collaborator_id).user.id))

        project.save()

        return redirect('project_details', id=project.id)

    user_profile = Profile.objects.get(user=request.user)
    tasks = sorted(Task.objects.filter(project=project), key=lambda x: x.deadline)
    edit_mode = request.GET.get('edit')

    if edit_mode is not None:
        edit_mode = True
    else:
        edit_mode = False

    context = {
        'project': project,
        'user_profile': user_profile,
        'tasks': tasks,
        'collaborators': Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(
            user__username__startswith='admin'),
        'edit_mode': edit_mode,
        'clients': Client.objects.all(),
        'segment': 'projects'
    }

    return render(request, 'home/project.html', context)


def edit(request, id):
    project = Project.objects.get(id=id)
    if request.method == 'POST':
        return redirect('project_details', id=project.id)


def change_picture(request, id):
    project = Project.objects.get(id=id)

    if request.method == 'POST':
        file = request.FILES['projectPicture']
        previous_file = project.img

        if 'placeholder' not in previous_file.name and file:
            previous_file.delete(save=False)

        project.img = file
        project.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


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
    file_path = uploaded_file.file
    file_path.delete(save=False)
    uploaded_file.value = 0
    uploaded_file.save()
    uploaded_file.delete()

    return redirect('project_details', id=project_id)


def download_file(request, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_name = uploaded_file.file.name
    file_content = default_storage.open(file_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'
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
            created_by=request.user,
            owner=User.objects.get(id=request.POST['taskOwner']) if request.POST.get('taskOwner') else None
        )

        task.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


def delete_task(request, project_id, task_id):
    project = Project.objects.get(id=project_id)
    task = Task.objects.get(id=task_id, project=project)
    task.delete()
    project.save(update_tasks=True)

    return redirect('project_details', id=project_id)


def edit_task(request, project_id, task_id):
    task = Task.objects.get(id=task_id)
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        task.title = request.POST.get('taskTitleEdit', task.title)
        task.description = request.POST.get('taskDescriptionEdit', task.description)
        task.deadline = request.POST.get('taskDeadlineEdit', task.deadline)
        task.priority = int(request.POST.get('taskPriorityEdit', task.priority))
        task.owner = User.objects.get(id=request.POST['taskOwnerEdit']) if request.POST.get('taskOwnerEdit') else task.owner
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


def add_link(request, project_id):
    project = Project.objects.get(id=project_id)

    if request.method == 'POST':
        link = Link(
            project=project,
            title=request.POST.get('linkTitle'),
            path=request.POST.get('linkURL'),
            created_by=request.user,
        )

        link.save()

        return redirect('project_details', id=project.id)

    return redirect('project_details', id=project.id)


def delete_link(request, project_id, link_id):
    project = Project.objects.get(id=project_id)
    link = Link.objects.get(id=link_id, project=project)
    link.delete()

    return redirect('project_details', id=project_id)
