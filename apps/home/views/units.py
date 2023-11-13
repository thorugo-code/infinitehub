from django.shortcuts import render, redirect
from apps.home.models import Profile, Unit
from django.core.paginator import Paginator
from django.db.models import Q


def get_paginated_clients(request, order_by):
    # query = Q()
    # clients_list = Client.objects.filter(query)
    units_list = Unit.objects.all()

    if order_by is not None:
        paginator = Paginator(units_list.order_by(order_by), 6)
    else:
        paginator = Paginator(units_list, 6)

    page = request.GET.get('page')

    clients = paginator.get_page(page)
    return paginator, clients


def home(request, order_by=None):
    paginator, units = get_paginated_clients(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'units': units,
    }

    return render(request, 'home/units_home.html', context)


def create(request):
    if request.method == 'POST':
        unit = Unit(
            name=request.POST['name'],
            cnpj=request.POST['cnpj'],
            area=request.POST['area'],
            location=request.POST['location'],
        )

        unit.save()

    return redirect('clients_home')

