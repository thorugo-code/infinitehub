from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from decouple import config


def home(request):
    return render(request, 'members/home.html')


def detail(request, identifier):
    user = User.objects.filter(
        username__startswith=identifier,
        is_active=True,
        username__endswith=config('COLLABORATORS_KEY', default='')
    )

    if user and user.count() == 1:
        return render(request, 'members/home.html', {'user': user[0]})

    return redirect('members_home')
