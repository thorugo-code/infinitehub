from django.shortcuts import render, redirect
from apps.home.models import Profile, Office
from django.core.paginator import Paginator


def get_permission(request, permission_type, model='office'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def get_paginated_clients(request, order_by):
    # query = Q()
    # clients_list = Client.objects.filter(query)
    offices_list = Office.objects.all()

    if order_by is not None:
        paginator = Paginator(offices_list.order_by(order_by), 6)
    else:
        paginator = Paginator(offices_list, 6)

    page = request.GET.get('page')

    clients = paginator.get_page(page)
    return paginator, clients


def home(request, order_by=None):
    if not get_permission(request, 'view'):
        return render(request, 'home/page-404.html')

    paginator, offices = get_paginated_clients(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'offices': offices,
        'segment': 'administrative',
    }

    return render(request, 'home/offices_home.html', context)


def create(request):
    if not get_permission(request, 'add'):
        return render(request, 'home/page-404.html')

    if request.method == 'POST':
        office = Office(
            name=request.POST['name'],
            cnpj=request.POST['cnpj'],
            location=request.POST['address'],
            description=request.POST['description'],
        )

        office.save()

    return redirect('offices_home')


def delete(request, office_id):
    if not get_permission(request, 'delete'):
        return render(request, 'home/page-404.html')

    office = Office.objects.get(id=office_id)
    office.delete()

    return redirect('offices_home')


def edit(request, office_id):
    if not get_permission(request, 'change'):
        return render(request, 'home/page-404.html')

    office = Office.objects.get(id=office_id)

    if request.method == 'POST':
        office.name = request.POST.get('name', office.name)
        office.cnpj = request.POST.get('cnpj', office.cnpj)
        office.description = request.POST.get('description', office.description)
        office.location = request.POST.get('address', office.location)

        office.save()

    return redirect('offices_home')
