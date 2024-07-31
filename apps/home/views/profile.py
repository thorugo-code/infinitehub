import datetime
import os
import json
from core.settings import CORE_DIR
from django.contrib import messages
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.core.files.storage import default_storage
from apps.home.models import Profile, Task, Office, Document, UploadedFile
from django.db.models import Q


def details(request):
    user = request.user
    if user.has_perm('home.view_document'):
        shared_documents = Document.objects.filter(user=user)
    else:
        shared_documents = Document.objects.filter(shared=True, user=user)

    query = Q(owner=user) | Q(subtasks__owner=user)

    all_tasks = Task.objects.filter(query)
    tasks_to_do = all_tasks.filter(completed=False)
    tasks_completed = all_tasks.filter(completed=True)
    all_projects = user.assigned_projects.all()
    projects_to_do = all_projects.filter(finished=False)
    projects_completed = all_projects.filter(finished=True)

    context = {
        'tasks_count': all_tasks.count(),
        'user_profile': Profile.objects.get(user=user),
        'shared_documents': shared_documents,
        'tasks': sorted(tasks_to_do, key=lambda x: x.deadline if x.deadline else datetime.date.max),
        'projects': reversed(sorted(projects_to_do, key=lambda x: x.completition)),
        'completed_tasks': tasks_completed.count(),
        'completed_tasks_percentage': (tasks_completed.count() / all_tasks.count()) * 100 if all_tasks.count() > 0 else 0,
        'completed_projects': projects_completed.count(),
        'completed_projects_percentage': (projects_completed.count() / all_projects.count()) * 100 if all_projects.count() > 0 else 0,
        'segment': 'profile',
    }

    return render(request, 'home/profile/home.html', context)


def change_picture(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        file = request.FILES['profilePicture']
        previous_file = user_profile.avatar

        if 'placeholder' not in previous_file.name and file:
            previous_file.delete(save=False)

        user_profile.avatar = file
        user_profile.save()

        return redirect('profile')

    return redirect('profile')


def edit(request):
    if request.method == "POST":
        user_object = User.objects.get(username=request.user.username)

        user_object.first_name = request.POST['first_name'].title()
        user_object.last_name = request.POST['last_name'].title()

        profile = Profile.objects.get(user=request.user)
        profile.office = Office.objects.get(id=request.POST['office']) if request.POST.get(
            'office') else profile.office
        profile.street = request.POST.get('street', profile.street)
        profile.street_number = request.POST.get('street_number', profile.street_number)
        profile.city = request.POST.get('city', profile.city)
        profile.state = request.POST.get('state', profile.state)
        profile.country = request.POST.get('country', profile.country)
        profile.about = request.POST.get('about', profile.about)
        profile.first_access = False
        profile.avatar = request.FILES.get('avatar', profile.avatar)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.birthday = request.POST.get('birthday', profile.birthday)
        profile.position = request.POST.get('position', profile.position)

        profile.website = request.POST.get('website', profile.website)
        profile.linkedin = request.POST.get('linkedin', profile.linkedin)
        profile.twitter = request.POST.get('twitter', profile.twitter)
        profile.facebook = request.POST.get('facebook', profile.facebook)
        profile.instagram = request.POST.get('instagram', profile.instagram)

        user_object.save()
        profile.save()

        return redirect("profile")

    else:
        user_profile = Profile.objects.get(user=request.user)

        context = {
            "world": json.load(open(f'{CORE_DIR}/apps/static/assets/world.json', 'r', encoding='utf-8')),
            "offices": Office.objects.all(),
            "user": user_profile,
            "edit_profile": True,
        }

        return render(request, "home/profile/wizard.html", context)


def delete_file(request, file_id):
    uploaded_file = UploadedFile.objects.get(id=file_id)
    file_path = uploaded_file.file
    file_path.delete(save=False)
    uploaded_file.value = 0
    uploaded_file.save()

    uploaded_file.delete()

    return redirect('profile')


def download_qrcode(request):
    user = request.user
    profile = Profile.objects.get(user=user)
    qrcode = profile.qrcode

    if qrcode:
        file_name = qrcode.name
        file_content = default_storage.open(file_name).read()
        response = HttpResponse(file_content, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'
        return response
    else:
        messages.error(request, 'QR Code not found.')

    return redirect('profile')

