from django.shortcuts import render, redirect
from apps.home.models import Profile, Client
from django.core.paginator import Paginator
from django.db.models import Q


def get_permission(request, permission_type, model='client'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def get_paginated_clients(request, order_by):
    # query = Q()
    # clients_list = Client.objects.filter(query)
    clients_list = Client.objects.all()

    if order_by is not None:
        paginator = Paginator(clients_list.order_by(order_by), 6)
    else:
        paginator = Paginator(clients_list, 6)

    page = request.GET.get('page')

    clients = paginator.get_page(page)
    return paginator, clients


def home(request, order_by=None):
    if not get_permission(request, 'view'):
        return render(request, 'home/page-404.html')

    paginator, clients = get_paginated_clients(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'clients': clients,
    }

    return render(request, 'home/clients_home.html', context)


def create(request):
    if not get_permission(request, 'add'):
        return render(request, 'home/page-404.html')

    if request.method == 'POST':
        client = Client(
            name=request.POST.get('name', ''),
            cnpj=request.POST.get('cnpj', ''),
            email=request.POST.get('email', ''),
            phone=request.POST.get('phone', ''),
            area=request.POST.get('area', ''),
            location=request.POST.get('address', ''),
            description=request.POST.get('about', ''),
        )

        client.save()

    return redirect('clients_home')


def edit(request, client_id):
    if not get_permission(request, 'change'):
        return render(request, 'home/page-404.html')

    if request.method == 'POST':
        client = Client.objects.get(id=client_id)

        client.name = request.POST.get('name', client.name)
        client.cnpj = request.POST.get('cnpj', client.cnpj)
        client.email = request.POST.get('email', client.email)
        client.phone = request.POST.get('phone', client.phone)
        client.area = request.POST.get('area', client.area)
        client.location = request.POST.get('address', client.location)
        client.description = request.POST.get('about', client.description)

        client.save()

    return redirect('clients_home')


def delete(request, client_id):
    if not get_permission(request, 'delete'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(id=client_id)
    client.delete()

    return redirect('clients_home')

