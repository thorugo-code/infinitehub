from django.shortcuts import render, redirect
from apps.home.models import UploadedFile, Profile, Task, Document


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
        'uploaded_documents': Document.objects.filter(user=user, uploaded_by=user).count(),
        'uploaded_documents_percentage': (Document.objects.filter(user=user,
                                                                  uploaded_by=user).count() / Document.objects.filter(
            user=user).count()) * 100 if Document.objects.filter(user=user).count() > 0 else 0,
        'user_files': user_files,
        'user_files_number': user_files_count
    }

    if request.method == 'POST':
        user_profile.address = request.POST.get('address', user_profile.address)
        user_profile.city = request.POST.get('city', user_profile.city)
        user_profile.state = request.POST.get('state', user_profile.state)
        user_profile.country = request.POST.get('country', user_profile.country)
        user_profile.postal_code = request.POST.get('postal-code', user_profile.postal_code)

        user_profile.about = request.POST.get('about-user', user_profile.about)

        user_profile.save()

        redirect('profile')

    return render(request, 'home/profile.html', context)


def change_picture(request):
    user_profile = Profile.objects.get(user=request.user)

    if request.method == 'POST':
        file = request.FILES['profilePicture']
        user_profile.avatar = file
        user_profile.save()

        return redirect('profile')

    return redirect('profile')
