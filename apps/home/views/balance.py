import unittest.mock

from django.shortcuts import render, redirect
from apps.home.models import Profile, Unit


def home(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/balance.html', context)


def bills(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'units': Unit.objects.all(),
    }

    return render(request, 'home/bills.html', context)


def new_bill(request, type, redirect_to='balance_page'):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
    }

    return redirect('balance_page')
