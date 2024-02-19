import datetime
from django.db.models import Q
from django.shortcuts import render, redirect
from apps.home.models import Profile, Client, Office, Document


def check_expired_documents():
    expired_documents = Document.objects.filter(Q(expiration__lt=datetime.datetime.now().date()) & Q(expired=False))
    for doc in expired_documents:
        doc.expired = True
        doc.save()


def get_permission(request, permission_type, model='client'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def home(request, filters=None, sorted_by=None, sort_type=None):
    if not get_permission(request, 'view'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    clients = filter_clients_objects(request, filters)
    clients = sort_clients_objects(clients, sorted_by, sort_type)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'clients': clients,
        'offices': Office.objects.all(),
        'filters': filters,
        'sorted_by': sorted_by,
        'sort_type': sort_type,
    }

    return render(request, 'home/clients-list.html', context)


def create(request):
    if not get_permission(request, 'add'):
        return render(request, 'home/page-404.html')

    if request.method == 'POST':
        client = Client(
            name=request.POST.get('name', ''),
            cnpj=request.POST.get('cnpj', ''),
            area=request.POST.get('area', ''),
            office=Office.objects.get(id=request.POST['office']) if request.POST.get('office') else None,
            location=request.POST.get('address', ''),
            contact_email=request.POST.get('contact_email', ''),
            phone=request.POST.get('phone', ''),
            xml_email=request.POST.get('xml_email', ''),
            description=request.POST.get('about', ''),
        )

        client.save()

        return redirect('client_details', slug=client.slug)

    return redirect('clients_home')


def delete(request, client_id):
    if not get_permission(request, 'delete'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(id=client_id)
    client.delete()

    return redirect('clients_home')


def details(request, slug):
    if not get_permission(request, 'change'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    if request.method == 'POST':
        client.name = request.POST.get('name', client.name)
        client.cnpj = request.POST.get('cnpj', client.cnpj)
        client.area = request.POST.get('area', client.area)
        client.office = Office.objects.get(id=request.POST['office']) if request.POST.get('office') else client.office
        client.location = request.POST.get('address', client.location)
        client.contact_email = request.POST.get('contact_email', client.contact_email)
        client.phone = request.POST.get('phone', client.phone)
        client.xml_email = request.POST.get('xml_email', client.xml_email)
        client.description = request.POST.get('about', client.description)

        client.save()

        return redirect('client_details', slug=client.slug)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
    }

    return render(request, 'home/client-page.html', context)


def sort(request):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    print(f'sorted_by: {sorted_by} | sort_type: {sort_type} | filters: {filters}')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_clients', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '':
        return redirect('sorted_clients', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_clients', filters=filters)
    else:
        return redirect('clients_home')


def filter_clients_objects(request, filters):
    clients = Client.objects.all()

    if filters:
        filters_list = filters.split('&')

        office = 'all'

        for item in filters_list:
            office = item.split('=')[1] if item.startswith('office') else office

        if office != 'all':
            clients = clients.filter(office=office if office else None)

    return clients


def sort_clients_objects(clients, sorted_by, sort_type):
    if sorted_by is not None:
        sorted_by = sorted_by.replace('-', '_')
    else:
        sorted_by = ''

    if sorted_by == 'office':
        if sort_type == 'desc':
            clients = sorted(clients, key=lambda client: client.office.name if client.office else '')
        else:
            clients = sorted(clients, key=lambda client: client.office.name if client.office else 'z')
    else:
        clients = sorted(clients, key=lambda client: getattr(client, sorted_by, ''))

    if sort_type == 'desc':
        clients = reversed(clients)

    return clients


def filter_clients(request):
    office = request.POST['office']

    filter_list = [
        f'office={office}' if office != 'all' else '%',
    ]

    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    if request.POST['sort_by'] != 'None' and filter_string != '%':
        return redirect('sorted_filtered_clients',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_clients',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'])
    elif filter_string == '%':
        return redirect('clients_home')
    else:
        return redirect('filtered_clients', filters=filter_string)
