from django.shortcuts import render, redirect
from apps.home.models import Profile, Client
from django.core.paginator import Paginator
from django.db.models import Q


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
    paginator, clients = get_paginated_clients(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'clients': clients,
    }

    return render(request, 'home/clients_home.html', context)


def create(request):
    if request.method == 'POST':
        client = Client(
            name=request.POST['name'],
            cnpj=request.POST['cnpj'],
            area=request.POST['area'],
            location=request.POST['location'],
            description=request.POST['about'],
        )

        client.save()

    return redirect('clients_home')


def delete(request, client_id):
    client = Client.objects.get(id=client_id)
    client.delete()

    return redirect('clients_home')

