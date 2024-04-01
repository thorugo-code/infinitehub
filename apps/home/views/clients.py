import datetime
from django.db.models import Q
from django.shortcuts import render, redirect
from apps.home.models import Profile, Client, Office, Document, Bill, BillInstallment
from django.contrib.auth.models import User
from apps.home.views.balance import INCOME_CATEGORIES, EXPENSE_CATEGORIES, unmask_money


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


def delete(request, slug):
    if not get_permission(request, 'delete'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)
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


def documents_page(request, slug):
    if not get_permission(request, 'view', 'document'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
        'documents': Document.objects.filter(client=client),
    }

    return render(request, 'home/client-documents.html', context)


def new_document(request, slug):
    if not get_permission(request, 'add', 'document'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    redirect_to = request.POST.get('redirect_to', 'client_details')

    if request.method == 'POST':
        expiration = request.POST.get('expiration', None)
        document = Document(
            client=client,
            uploaded_by=User.objects.get(username=request.user.username),
            name=request.POST.get('name', ''),
            expiration=expiration if expiration else None,
            category=request.POST.get('category', ''),
            description=request.POST.get('description', ''),
            file=request.FILES['file'],
        )

        document.save()

    return redirect(redirect_to, slug=client.slug)


def balance_page(request, slug):
    if not get_permission(request, 'view', 'document'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
        'documents': Bill.objects.filter(client=client),
        'income_categories': sorted(INCOME_CATEGORIES),
        'expense_categories': sorted(EXPENSE_CATEGORIES),
        'offices': Office.objects.all(),
    }

    return render(request, 'home/client-balance.html', context)


def new_bill(request, slug):
    if not get_permission(request, 'add', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        bill = Bill(
            # Foreign Keys
            client=Client.objects.get(slug=slug),
            office=Office.objects.get(id=request.POST['office_id']) if request.POST.get('office_id') != '' else None,
            created_by=request.user,
            # Char Fields
            title=request.POST.get('title', ''),
            category=request.POST.get('category', ''),
            method=request.POST.get('method', ''),
            origin=request.POST.get('origin', ''),
            # Date Fields
            due_date=request.POST.get('due_date', None) if request.POST.get('due_date', None) != '' else None,
            # Money Fields
            total=unmask_money(request.POST.get('total', ''), currency),
            # Integer Fields
            installments_number=request.POST.get('installments', 0),
            # File Fields
            proof=request.FILES.get('proof', None),
        )

        status = request.POST.get('status', 'Pending')
        if 'Paid' in status:
            bill.paid = True
            bill.paid_at = datetime.datetime.now()

        if 'reconciled' in status:
            bill.reconciled = True

        bill.save()

        if request.POST.get('installments') and request.POST.get('installments_value'):
            installments = request.POST.get('installments')
            installments_value = unmask_money(request.POST.get('installments_value', ''), currency)
            # installments_date = request.POST.get('installments_date', None)

            for i in range(1, int(installments) + 1):
                installment = BillInstallment(
                    bill=bill,
                    partial_id=i,
                    value=installments_value,
                    # due_date=installments_date,
                )
                installment.save()

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('client_balance', slug=slug)
        # return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    # elif sorted_by != '' and sorted_by != 'None':
    #     return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    # elif filters != 'None':
    #     return redirect('filtered_bills', filters=filters)
    else:
        return redirect('client_balance', slug=slug)


def delete_bill(request, slug, bill_id):
    if not get_permission(request, 'delete', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    file = bill.proof
    if file:
        file.delete(save=False)

    bill.delete()

    return redirect('client_balance', slug=slug)


def edit_bill(request, slug, bill_id):
    if not get_permission(request, 'change', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    if request.method == 'POST':
        due_date = request.POST.get('due_date', bill.due_date)
        currency = request.POST.get('currency', 'USD')
        bill.client = Client.objects.get(slug=request.POST['client_slug'])
        bill.office = Office.objects.get(id=request.POST['office_id']) if request.POST.get(
            'office_id') else bill.office if request.POST.get('office_id') != '' else None
        bill.title = request.POST.get('title', bill.title)
        bill.category = request.POST.get('category', bill.category)
        bill.method = request.POST.get('method', bill.method)
        bill.due_date = due_date if due_date != '' else None
        bill.total = unmask_money(request.POST['total'], currency) if request.POST.get('total') else bill.total

        installments_number_from_form = int(request.POST.get('installments', 0))
        installments_value_from_form = unmask_money(request.POST.get('installments_value', ''), currency)
        if installments_number_from_form != bill.installments_number and installments_number_from_form > 1:
            installments = BillInstallment.objects.filter(bill=bill)
            installments.delete()
            bill.installments_number = installments_number_from_form
            for i in range(1, installments_number_from_form + 1):
                installment = BillInstallment(
                    bill=bill,
                    partial_id=i,
                    value=installments_value_from_form,
                    # due_date=request.POST.get('installments_date', None),
                )
                installment.save()

        elif installments_number_from_form == bill.installments_number and installments_value_from_form != bill.installments.first().value:
            installments = BillInstallment.objects.filter(bill=bill)
            for installment in installments:
                installment.value = installments_value_from_form
                installment.save()

        if request.FILES.get('proof') and request.FILES.get('proof') != bill.proof and bill.proof:
            file = bill.proof
            if file:
                file.delete(save=False)
            bill.proof = request.FILES['proof']
        else:
            bill.proof = request.FILES.get('proof', bill.proof)

        bill.save()

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('client_balance', slug=slug)
        # return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    # elif sorted_by != '' and sorted_by != 'None':
    #     return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    # elif filters != 'None':
    #     return redirect('filtered_bills', filters=filters)
    else:
        return redirect('client_balance', slug=slug)
