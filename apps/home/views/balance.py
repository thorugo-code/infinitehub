from django.shortcuts import render, redirect
from apps.home.models import Profile


def page(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/balance.html', context)
