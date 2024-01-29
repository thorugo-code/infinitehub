from django.shortcuts import render, redirect
from apps.home.models import UploadedFile, Profile, Task, Office
from django.contrib.auth.models import User
from core.settings import CORE_DIR
import json


def details(request):
    user = request.user
    user_profile = Profile.objects.get(user=user)
    user_files = UploadedFile.objects.filter(uploaded_by=user)
    user_files_count = user_files.count()

    context = {
        'user_profile': user_profile,
        'completed_tasks': Task.objects.filter(created_by=user, completed=True).count(),
        'completed_tasks_percentage': (Task.objects.filter(created_by=user,
                                                           completed=True).count() / Task.objects.filter(
            created_by=user).count()) * 100 if Task.objects.filter(created_by=user).count() > 0 else 0,
        'project_files': UploadedFile.objects.filter(uploaded_by=user, project__isnull=False).count(),
        'project_files_percentage': (UploadedFile.objects.filter(uploaded_by=user,
                                                                 project__isnull=False).count() / UploadedFile.objects.filter(
            uploaded_by=user).count()) * 100 if UploadedFile.objects.filter(uploaded_by=user).count() > 0 else 0,
        'user_files': user_files,
        'user_files_number': user_files_count
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

        profile.save()
        user_object.save()

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

