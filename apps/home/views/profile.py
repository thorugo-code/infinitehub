from django.shortcuts import render, redirect
from apps.home.models import Profile, Task, Office, Document, UploadedFile
from django.contrib.auth.models import User
from core.settings import CORE_DIR
import json
import os


def details(request):
    user = request.user
    shared_documents = Document.objects.filter(shared=True) | Document.objects.filter(category='Payslip')

    all_tasks = Task.objects.filter(owner=user)
    tasks_to_do = all_tasks.filter(completed=False)
    tasks_completed = all_tasks.filter(completed=True)
    all_projects = user.assigned_projects.all()
    projects_to_do = all_projects.filter(finished=False)
    projects_completed = all_projects.filter(finished=True)

    context = {
        'user_profile': Profile.objects.get(user=user),
        'shared_documents': shared_documents,
        'tasks': sorted(tasks_to_do, key=lambda x: x.deadline),
        'projects': reversed(sorted(projects_to_do, key=lambda x: x.completition)),
        'completed_tasks': tasks_completed.count(),
        'completed_tasks_percentage': (tasks_completed.count() / all_tasks.count()) * 100 if all_tasks.count() > 0 else 0,
        'completed_projects': projects_completed.count(),
        'completed_projects_percentage': (projects_completed.count() / all_projects.count()) * 100 if all_projects.count() > 0 else 0,
    }

    return render(request, 'home/profile.html', context)


def change_picture(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        file = request.FILES['profilePicture']
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

        return render(request, "home/profile-wizard.html", context)


def delete_file(request, file_id):
    uploaded_file = UploadedFile.objects.get(id=file_id)
    file_path = uploaded_file.file.path
    if os.path.exists(file_path):
        os.remove(file_path)

    uploaded_file.value = 0
    uploaded_file.save()

    uploaded_file.delete()

    return redirect('profile')

