from django.shortcuts import render, redirect
from apps.home.models import Profile, Unit
from django.core.paginator import Paginator
from django.db.models import Q


def get_paginated_clients(request, order_by):
    # query = Q()
    # clients_list = Client.objects.filter(query)
    offices_list = Unit.objects.all()

    if order_by is not None:
        paginator = Paginator(offices_list.order_by(order_by), 6)
    else:
        paginator = Paginator(offices_list, 6)

    page = request.GET.get('page')

    clients = paginator.get_page(page)
    return paginator, clients


def home(request, order_by=None):
    paginator, offices = get_paginated_clients(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'offices': offices,
    }

    return render(request, 'home/offices_home.html', context)


def create(request):
    if request.method == 'POST':
        office = Unit(
            name=request.POST['name'],
            cnpj=request.POST['cnpj'],
            area=request.POST['area'],
            location=request.POST['location'],
        )

        office.save()

    return redirect('offices_home')


def delete(request, unit_id):
    office = Unit.objects.get(id=unit_id)
    office.delete()

    return redirect('offices_home')
