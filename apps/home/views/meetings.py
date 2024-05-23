from django.shortcuts import render
from django.shortcuts import redirect
from django.contrib.auth.models import User
from apps.home.models import Meeting, Project, Task, Profile
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


def home(request):
    user = request.user
    meetings_list = Meeting.objects.all().order_by('-start')
    meetings, paginator = get_paginated_meetings(request, meetings_list)
    context = {
        'user_profile': user.profile,
        'meetings_list': meetings,
        'paginator': paginator,
    }

    return render(request, 'home/meetings.html', context)


def details(request, meeting_id):
    meeting = Meeting.objects.get(id=meeting_id)
    requests = meeting.tasks.all()

    if request.method == 'POST':
        project_id = request.POST.get('project')
        project = Project.objects.get(id=project_id)
        meeting.project = project
        meeting.client = project.client
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

    return render(request, 'home/meeting-details.html', context)


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

