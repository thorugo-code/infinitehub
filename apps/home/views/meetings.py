from datetime import datetime
from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from apps.home.models import Meeting, Project, Task, Profile, SubTask
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger


def get_paginated_meetings(request, meetings_list):
    page = request.GET.get('page', 1)
    paginator = Paginator(meetings_list, 8)
    try:
        meetings = paginator.page(page)
    except PageNotAnInteger:
        meetings = paginator.page(1)
    except EmptyPage:
        meetings = paginator.page(paginator.num_pages)

    return meetings, paginator


###########################################################


def home(request):
    user = request.user
    meetings_list = Meeting.objects.all().order_by('-start')
    meetings, paginator = get_paginated_meetings(request, meetings_list)
    context = {
        'user_profile': user.profile,
        'meetings_list': meetings,
        'paginator': paginator,
    }

    return render(request, 'home/meetings/home.html', context)


def details(request, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    requests = meeting.tasks.all()

    if request.method == 'POST':
        project_id = request.POST.get('project', None)
        if project_id == '':
            project = None
        elif project_id is not None:
            project = Project.objects.get(id=project_id)
        else:
            project = meeting.project

        meeting.project = project

        if project is not None:
            meeting.client = project.client
        else:
            meeting.client = None

        meeting.save()

        for task in meeting.tasks.all():
            task.project = project
            task.save()

    context = {
        'meeting': meeting,
        'user_profile': request.user.profile,
        'requests_to_attend': requests.filter(completed=False).count(),
        'projects': Project.objects.filter(archive=False).order_by('title'),
        'segment': 'meetings',
        'collaborators': Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(
            user__username__startswith='admin'),
    }

    return render(request, 'home/meetings/details.html', context)


###########################################################


def edit_task(request, meeting_id, task_id):
    task = Task.objects.get(id=task_id)

    if request.method == 'POST':
        post_deadline = request.POST.get('taskDeadlineEdit')
        task.title = request.POST.get('taskTitleEdit', task.title)
        task.project = Project.objects.get(id=request.POST['taskProjectEdit']) if request.POST.get('taskProjectEdit') else task.project
        task.description = request.POST.get('taskDescriptionEdit', task.description)
        task.deadline = post_deadline if post_deadline else task.deadline
        task.priority = int(request.POST.get('taskPriorityEdit', task.priority))
        task.owner = User.objects.get(id=request.POST['taskOwnerEdit']) if request.POST.get('taskOwnerEdit') else task.owner
        task.save()

    return redirect('meeting_details', meeting_id=meeting_id)


def delete_task(request, meeting_id, task_id):
    if request.method == "POST":
        task = Task.objects.get(id=task_id)
        task.delete()

    return redirect('meeting_details', meeting_id=meeting_id)


def change_task_status(request, meeting_id, task_id):
    task = Task.objects.get(id=task_id)

    if request.method == 'POST':
        if task.completed:
            task.completed = False
            task.completed_by = None
            task.completed_at = None
        else:
            task.completed = True
            task.completed_by = request.user
            task.completed_at = datetime.now()
            task.subtasks.filter(completed=False).update(
                completed=True, completed_by=request.user, completed_at=datetime.now()
            )

        task.save()

    return redirect('meeting_details', meeting_id=meeting_id)


###########################################################


def submit_subtask(request, meeting_id, task_id):
    task = Task.objects.get(id=task_id)

    if request.method == 'POST':
        deadline = request.POST.get('subtaskDeadline', None)
        if deadline == '':
            deadline = None

        subtask = SubTask(
            task=task,
            title=request.POST.get('subtaskTitle'),
            priority=int(request.POST.get('subtaskPriority')),
            deadline=deadline,
            owner=User.objects.get(id=request.POST['subtaskOwner']) if request.POST.get('subtaskOwner') else None,
            description=request.POST.get('subtaskDescription'),
            created_by=request.user,
        )

        subtask.save()

    return redirect('meeting_details', meeting_id=meeting_id)


def delete_subtask(request, meeting_id, task_id, subtask_id):
    subtask = SubTask.objects.get(id=subtask_id, task__id=task_id)
    subtask.delete()
    subtask.task.project.save(update_tasks=True)

    return redirect('meeting_details', meeting_id=meeting_id)


def edit_subtask(request, meeting_id, task_id, subtask_id):
    subtask = SubTask.objects.get(id=subtask_id, task__id=task_id)

    if request.method == 'POST':
        post_deadline = request.POST.get('taskDeadlineEdit')
        subtask.title = request.POST.get('taskTitleEdit', subtask.title)
        subtask.description = request.POST.get('taskDescriptionEdit', subtask.description)
        subtask.deadline = post_deadline if post_deadline else subtask.deadline
        subtask.priority = int(request.POST.get('taskPriorityEdit', subtask.priority))
        subtask.owner = User.objects.get(id=request.POST['taskOwnerEdit']) if request.POST.get('taskOwnerEdit') else subtask.owner
        subtask.save()

    return redirect('meeting_details', meeting_id=meeting_id)


def change_subtask_status(request, meeting_id, task_id, subtask_id):
    subtask = SubTask.objects.get(id=subtask_id, task__id=task_id)

    if request.method == 'POST':
        if subtask.completed:
            subtask.completed = False
            subtask.completed_by = None
            subtask.completed_at = None
        else:
            subtask.completed = True
            subtask.completed_by = request.user
            subtask.completed_at = datetime.now()

        subtask.save()

    return redirect('meeting_details', meeting_id=meeting_id)


