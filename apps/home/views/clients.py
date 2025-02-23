import json
from datetime import datetime, timedelta
from django.db.models import Q, Sum, F
from django.shortcuts import render, redirect, get_object_or_404
from apps.home.models import Profile, Client, Office, Document, Bill, BillInstallment, BillProof, Branch
from apps.home.views.balance import INCOME_CATEGORIES, EXPENSE_CATEGORIES, unmask_money, check_late_bills
from django.core.files.storage import default_storage
from django.http import HttpResponse, JsonResponse
from core.settings import CORE_DIR
from djmoney.money import Money


MONTHS = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4,
    'May': 5, 'Jun': 6, 'Jul': 7, 'Aug': 8,
    'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}


def check_expired_documents():
    expired_documents = Document.objects.filter(Q(expiration__lt=datetime.now().date()) & Q(expired=False))
    for doc in expired_documents:
        doc.expired = True
        doc.save()

    unexpected_expired_documents = Document.objects.filter(
        Q(expiration__gt=datetime.now().date()) & Q(expired=True))
    for doc in unexpected_expired_documents:
        doc.expired = False
        doc.save()


def get_permission(request, permission_type, model='client'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def process_filters(request, page, slug, filters=None, order=None):
    if order is not None:
        sort_type = order
    else:
        sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None

    # if page == 'balance':
    #     sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    # elif page == 'documents':
    #     sort_type = 'asc' if request.POST.get('asc', None) else 'desc'
    # else:
    #     sort_type = None

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    if filters is None:
        filters_list = request.POST.get('filters', 'None')
    elif filters == '%':
        filters_list = 'None'
    else:
        filters_list = filters

    if sorted_by not in ['', 'None'] and filters_list != 'None':
        return redirect(f'sorted_filtered_client_{page}', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters_list)

    if sorted_by not in ['', 'None']:
        return redirect(f'sorted_client_{page}', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters_list != 'None':
        return redirect(f'filtered_client_{page}', slug=slug, filters=filters_list)
    else:
        return redirect(f'client_{page}', slug=slug)


############################################


def home(request, filters=None, sorted_by=None, sort_type=None):
    if not get_permission(request, 'view'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    clients = filter_clients_objects(request, filters)
    clients = sort_clients_objects(clients, sorted_by, sort_type)

    upcoming_query = (
        Q(client__in=clients) &
        Q(paid=False) &
        Q(due_date__lte=datetime.now().date() + timedelta(days=60))
    )

    current_month_index = datetime.now().month
    current_year = datetime.now().year
    start_month_index = (current_month_index - 6 + 12) % 12
    months_numbers = [(start_month_index + i) % 12 + 1 for i in range(6)]

    received_list = []
    paid_list = []

    for month in months_numbers:
        year = current_year
        if month > current_month_index:
            year -= 1

        query = (Q(paid_at__month=month) & Q(paid_at__year=year))

        at_sight = Bill.objects.filter(
            query & Q(installments_number=0) & Q(client__in=clients)
        ).distinct()

        income_bills = at_sight.filter(category__in=INCOME_CATEGORIES)
        expense_bills = at_sight.filter(category__in=EXPENSE_CATEGORIES)

        received_at_sight = sum([bill.partial for bill in income_bills])
        paid_at_sight = sum([bill.partial for bill in expense_bills])

        received_list.append(received_at_sight)
        paid_list.append(paid_at_sight)

        with_installments = Bill.objects.filter(
            (query | Q(partial__lt=F('total'))) & Q(installments_number__gt=1) & Q(client__in=clients)
        ).distinct()

        income_bills_installments = with_installments.filter(category__in=INCOME_CATEGORIES)
        expense_bills_installments = with_installments.filter(category__in=EXPENSE_CATEGORIES)

        received_installments = sum([
            installment.value
            for bill in income_bills_installments
            for installment in bill.installments.filter(paid_at__month=month, paid_at__year=year)
        ])

        paid_installments = sum([
            installment.value
            for bill in expense_bills_installments
            for installment in bill.installments.filter(paid_at__month=month, paid_at__year=year)
        ])

        received_list[-1] += received_installments
        paid_list[-1] += paid_installments

    context = {
        'upcoming_bills': Bill.objects.filter(upcoming_query).distinct(),
        'user_profile': Profile.objects.get(user=request.user),
        'clients': clients,
        'offices': Office.objects.all(),
        'filters': filters,
        'sorted_by': sorted_by,
        'sort_type': sort_type,
        'months_list': [list(MONTHS.keys())[(start_month_index + i) % 12] for i in range(6)],
        'received_list': [str(received)[2:].replace(',', '') for received in received_list],
        'paid_list': [str(paid)[2:].replace(',', '') for paid in paid_list],
        'income_categories': INCOME_CATEGORIES,
        'expense_categories': EXPENSE_CATEGORIES,
        'last_six_months_received': sum(received_list),
        'last_six_months_paid': sum(paid_list),
    }

    return render(request, 'home/clients/home.html', context)


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

    return sort(request)


def sort(request):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    if sort_type == 'desc':
        sort_type = request.POST.get('sort_type', 'desc') if request.POST.get('sort_type', 'desc') != 'None' else 'desc'
    filters = request.POST.get('filters', 'None')

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


############################################


def details(request, slug):
    if not get_permission(request, 'change'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    client = Client.objects.get(slug=slug)

    if request.method == 'POST':
        client.identification = request.POST.get('ID', client.identification)
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

    query = Q(client=client) & (Q(paid=True) | Q(installments__paid=True))

    client_bills = Bill.objects.filter(query).distinct()

    income_bills = client_bills.filter(category__in=INCOME_CATEGORIES)
    expense_bills = client_bills.filter(category__in=EXPENSE_CATEGORIES)
    total_income = sum([bill.partial for bill in income_bills])
    total_expense = sum([bill.partial for bill in expense_bills])

    last_month_bills = client_bills.filter(
        Q(paid_at__gte=datetime.now().date() - timedelta(days=30)) |
        Q(installments__paid_at__gte=datetime.now().date() - timedelta(days=30))
    )

    last_month_bills_income = last_month_bills.filter(category__in=INCOME_CATEGORIES)
    last_month_bills_expense = last_month_bills.filter(category__in=EXPENSE_CATEGORIES)
    total_last_month_income = sum([bill.partial for bill in last_month_bills_income])
    total_last_month_expense = sum([bill.partial for bill in last_month_bills_expense])

    if total_income + total_expense != 0 and total_income != 0:
        income_percentage = total_income / (total_income + total_expense) * 100
    else:
        income_percentage = 0

    if total_income + total_expense != 0 and total_expense != 0:
        expense_percentage = total_expense / (total_income + total_expense) * 100
    else:
        expense_percentage = 0

    last_month_balance = total_last_month_income - total_last_month_expense
    last_month_difference = abs((total_income - total_expense) - last_month_balance)

    if (last_month_difference != 0 and last_month_balance != 0 and
            not str(last_month_difference).endswith('$0.00') and not str(last_month_balance).endswith('$0.00')):
        last_month_percentage = last_month_balance / last_month_difference * 100
    else:
        last_month_percentage = 0

    bills_in_progress = Bill.objects.filter(
        client=client, paid=False, due_date__lt=datetime.now().date() + timedelta(days=40)
    ).order_by('due_date')

    context = {
        'currency': 'BRL',  # TODO: Change to currency variable when implemented
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
        'collaborators': Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(
            user__username__startswith='admin').exclude(user__username__startswith='hub'),
        'balance': total_income - total_expense,
        'income_percentage': round(income_percentage),
        'expense_percentage': round(expense_percentage),
        'last_month_balance': last_month_balance,
        'last_month_balance_percentage': round(last_month_percentage, 1),
        'income_categories': INCOME_CATEGORIES,
        'expense_categories': EXPENSE_CATEGORIES,
        'bills_in_progress': bills_in_progress,
        'offices': Office.objects.all(),
        'world': json.load(open(f'{CORE_DIR}/apps/static/assets/world.json', 'r', encoding='utf-8')),
        'highlight_documents': Document.objects.filter(client=client).order_by('-id')[:5],
    }

    return render(request, 'home/clients/details.html', context)


def change_picture(request, slug):
    if not get_permission(request, 'change'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    if request.method == 'POST':
        previous_avatar = client.avatar
        if 'placeholder' not in previous_avatar.name and request.FILES.get('avatar'):
            previous_avatar.delete(save=False)

        client.avatar = request.FILES.get('avatar', client.avatar)
        client.save()

        return redirect(request.POST.get('redirect_to', 'client_details'), slug=client.slug)

    return redirect('client_details', slug=client.slug)


def new_branch(request, slug):
    if not get_permission(request, 'add', 'branch'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    if request.method == 'POST':
        branch = Branch(
            client=client,
            name=request.POST.get('name', ''),
            country=request.POST.get('country', ''),
            state=request.POST.get('state', ''),
            city=request.POST.get('city', ''),
            address=request.POST.get('address', ''),
        )

        branch.save()

        return redirect('client_details', slug=client.slug)

    return redirect('client_details', slug=client.slug)


def edit_branch(request, slug, branch_id):
    if not get_permission(request, 'change', 'branch'):
        return render(request, 'home/page-404.html')

    branch = Branch.objects.get(id=branch_id)

    if request.method == 'POST':
        branch.identification = request.POST.get('ID', branch.identification)
        branch.name = request.POST.get('name', branch.name)
        branch.country = request.POST.get('country', branch.country)
        branch.state = request.POST.get('state', branch.state)
        branch.city = request.POST.get('city', branch.city)
        branch.address = request.POST.get('address', branch.address)

        branch.save()

        return redirect('client_details', slug=slug)

    return redirect('client_details', slug=slug)


def delete_branch(request, slug, branch_id):
    if not get_permission(request, 'delete', 'branch'):
        return render(request, 'home/page-404.html')

    branch = Branch.objects.get(id=branch_id)
    branch.delete()

    return redirect('client_details', slug=slug)


############################################


def documents_page(request, slug, sorted_by=None, sort_type=None, filters=None):
    if not get_permission(request, 'view', 'document'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    client = Client.objects.get(slug=slug)
    documents = filter_documents_objects(filters, slug)[0]
    if sorted_by is not None and sorted_by != 'regional':
        documents = documents.order_by(f'{"-" if sort_type == "desc" else ""}{sorted_by}')
    elif sorted_by is not None and sorted_by == 'regional':
        documents = documents.order_by(f'{"-" if sort_type == "desc" else ""}branch__name')

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
        'sorted_by': sorted_by,
        'sort_type': sort_type,
        'filters': filters,
        'documents': documents,
    }

    return render(request, 'home/clients/documents.html', context)


def new_document(request, slug, doc_id=None):
    if not get_permission(request, 'add', 'document'):
        return render(request, 'home/page-404.html')

    client = Client.objects.get(slug=slug)

    redirect_to = request.POST.get('redirect_to', 'client_details')

    if request.method == 'POST':
        expiration = request.POST.get('expiration', None)
        if not doc_id:
            document = Document(
                client=client,
                branch=Branch.objects.get(id=request.POST['branch_id']) if request.POST.get('branch_id') else None,
                uploaded_by=request.user,
                name=request.POST.get('name', ''),
                expiration=expiration if expiration else None,
                category=request.POST.get('category', ''),
                description=request.POST.get('description', ''),
                file=request.FILES['file'],
            )
        else:
            document = Document.objects.get(id=doc_id)
            document.branch = Branch.objects.get(id=request.POST['branch_id']) if request.POST.get('branch_id') else document.branch
            document.name = request.POST.get('name', document.name)
            document.expiration = expiration if expiration else None
            document.category = request.POST.get('category', document.category)
            document.description = request.POST.get('description', document.description)
            document.file = request.FILES['file'] if request.FILES.get('file') else document.file

        document.save()

        if redirect_to == 'client_documents':
            return process_filters(request, 'documents', slug)

    return redirect(redirect_to, slug=client.slug)


def delete_document(request, slug, document_id):
    if not get_permission(request, 'delete', 'document'):
        return render(request, 'home/page-404.html')

    if request.method == 'POST':
        redirect_to = request.POST.get('redirect_to', 'client_details')
        document = Document.objects.get(id=document_id)
        file = document.file
        if file:
            file.delete(save=False)

        document.delete()

        if redirect_to == 'client_documents':
            return process_filters(request, 'documents', slug)

    return redirect('client_details', slug=slug)


def download_document(request, slug, document_id):
    if not get_permission(request, 'view', 'document'):
        return render(request, 'home/page-404.html')

    document = get_object_or_404(Document, id=document_id)

    document_name = document.file.name
    file_content = default_storage.open(document_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document_name.split("/")[-1]}"'
    return response


def sort_and_filter_documents(request, slug):
    return process_filters(
        request, 'documents', slug,
        order='asc' if request.POST.get('asc', None) else 'desc'
    )


def filter_documents_objects(filters, slug):
    documents = Document.objects.filter(client=Client.objects.get(slug=slug))

    if filters is not None:
        filters_list = filters.split('&')

        category, regional = 'all', 'all'
        from_date, to_date = False, False

        for item in filters_list:
            from_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('from') else from_date
            to_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            category = item.split('=')[1] if item.startswith('category') else category
            regional = item.split('=')[1] if item.startswith('regional') else regional

            if from_date and to_date and from_date < to_date:
                documents = documents.filter(expiration__gte=from_date)
                documents = documents.filter(expiration__lte=to_date)
            elif from_date:
                documents = documents.filter(expiration__gte=from_date)
            elif to_date:
                documents = documents.filter(expiration__lte=to_date)

            if category != 'all':
                documents = documents.filter(category=category)

            if regional != 'all':
                documents = documents.filter(branch__id=regional)

    return documents, documents.order_by('-id').first().id if documents.count() > 0 else 0


def filter_documents(request, slug):
    from_date = request.POST['from']
    to_date = request.POST['to']
    category = request.POST['category']
    regional = request.POST['regional']

    filter_list = [
        f'from={from_date}' if from_date != '' and from_date != to_date else '%',
        f'to={to_date}' if to_date != '' and from_date != to_date else '%',
        f'category={category}' if category != 'all' else '%',
        f'regional={regional}' if regional != 'all' else '%',
    ]

    # Convert the list to a string with appropriate format, avoiding empty values
    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    return process_filters(request, 'documents', slug, filter_string)


############################################


def balance_page(request, slug, sorted_by=None, sort_type=None, filters=None):
    if not get_permission(request, 'view', 'document'):
        return render(request, 'home/page-404.html')

    check_late_bills()

    client = Client.objects.get(slug=slug)
    bills = filter_bill_objects(filters, slug)[0]
    if sorted_by is not None:
        if sorted_by == 'date':
            sort_string = 'created_at'
        elif sorted_by == 'expiration':
            sort_string = 'due_date'
        elif sorted_by == 'installments_value':
            bills = bills.annotate(installments_value=Sum('installments__value') / F('installments_number'))
            sort_string = sorted_by
        elif sorted_by == 'office':
            sort_string = 'office__name'
        elif sorted_by == 'payer':
            sort_string = 'payer__name'
        else:
            sort_string = sorted_by

        if sorted_by == 'code':
            bills = bills.order_by(f'{"-" if sort_type == "desc" else ""}code', f'{"-" if sort_type == "desc" else ""}link')
        elif sorted_by != 'None':
            bills = bills.order_by(f'{"-" if sort_type == "desc" else ""}{sort_string}')

    income_bills = bills.filter(category__in=INCOME_CATEGORIES)
    expense_bills = bills.filter(category__in=EXPENSE_CATEGORIES)

    pending_income = sum([bill.total - bill.partial for bill in income_bills])
    late_income = sum([sum([
        installment.value for installment in bill.installments.filter(
            due_date__lte=datetime.now().date()) if not installment.paid
    ]) if bill.late and bill.installments_number > 1 else bill.total if bill.late else 0 for bill in income_bills])

    pending_expense = sum([bill.total - bill.partial for bill in expense_bills])
    late_expense = sum([sum([
        installment.value for installment in bill.installments.filter(
            due_date__lte=datetime.now().date()) if not installment.paid
    ]) if bill.late and bill.installments_number > 1 else bill.total if bill.late else 0 for bill in expense_bills])

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'client': client,
        'bills': bills,
        'received': sum([bill.partial for bill in income_bills]),
        'income': sum([bill.total for bill in income_bills]),
        'pending_income': pending_income,
        'late_income': late_income,
        'paid': sum([bill.partial for bill in expense_bills]),
        'expense': sum([bill.total for bill in expense_bills]),
        'pending_expense': pending_expense,
        'late_expense': late_expense,
        'income_categories': sorted(INCOME_CATEGORIES),
        'expense_categories': sorted(EXPENSE_CATEGORIES),
        'offices': Office.objects.all(),
        'sorted_by': sorted_by,
        'sort_type': sort_type,
        'filters': filters,
        'min_value': str(bills.order_by('total').first().total)[2:].replace(',', '') if bills.count() > 0 else 0,
        'max_value': str(bills.order_by('-total').first().total)[2:].replace(',', '') if bills.count() > 0 else 0,
    }

    return render(request, 'home/clients/balance.html', context)


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
            payer=Branch.objects.get(id=request.POST['payer_id']) if request.POST.get('payer_id') != '' else None,
            office=Office.objects.get(id=request.POST['office_id']) if request.POST.get('office_id') != '' else None,
            created_by=request.user,
            # Char Fields
            title=request.POST.get('title', ''),
            category=request.POST.get('category', ''),
            method=request.POST.get('method', ''),
            origin=request.POST.get('origin', ''),
            code=request.POST.get('code', ''),
            # Date Fields
            due_date=request.POST.get('due_date', None) if request.POST.get('due_date', None) != '' else None,
            issue_date=request.POST['issue_date'],
            # Money Fields
            total=unmask_money(request.POST.get('total', ''), currency),
            # Integer Fields
            installments_number=request.POST.get('installments', 0),
            # URL Fields
            link=request.POST.get('link', None),
        )

        bill.save()

        if int(bill.installments_number) > 1 and request.POST.get('installments_value'):
            installments_value = unmask_money(request.POST.get('installments_value', ''), currency)
            bill.installments_frequency = request.POST.get('installments_frequency', 0)
            if bill.installments_frequency == '':
                bill.installments_frequency = 0

            for i in range(1, int(bill.installments_number) + 1):
                installment = BillInstallment(
                    bill=bill,
                    partial_id=i,
                    value=installments_value,
                    due_date=datetime.strptime(
                        str(bill.issue_date), "%Y-%m-%d"
                    ) + timedelta(days=int(bill.installments_frequency) * i) if bill.issue_date else None,
                )
                installment.save()

            bill.save()

        else:
            bill.installments_number = 0
            bill.installments_frequency = 0
            bill.save()

        for file in request.FILES.getlist('proofs'):
            BillProof.objects.create(
                bill=bill,
                file=file,
            ).save()

        return process_filters(request, 'balance', slug)

    return redirect('client_balance', slug=slug)


def delete_bill(request, slug, bill_id):
    if not get_permission(request, 'delete', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    Bill.objects.get(id=bill_id).delete()

    if request.POST.get('client_page', False):
        return redirect('client_details', slug=slug)

    return process_filters(request, 'balance', slug)


def edit_bill(request, slug, bill_id):
    if not get_permission(request, 'change', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        due_date = request.POST.get('due_date', bill.due_date)
        issue_date = request.POST.get('issue_date', bill.issue_date)
        paid_at = request.POST.get('paid_at', bill.paid_at)

        bill.client = Client.objects.get(slug=request.POST['client_slug'])
        bill.payer = Branch.objects.get(id=request.POST['payer_id']) if request.POST.get(
            'payer_id') else bill.payer if request.POST.get('payer_id') != '' else None
        bill.office = Office.objects.get(id=request.POST['office_id']) if request.POST.get(
            'office_id') else bill.office if request.POST.get('office_id') != '' else None
        bill.title = request.POST.get('title', bill.title)
        bill.category = request.POST.get('category', bill.category)
        bill.method = request.POST.get('method', bill.method)
        bill.origin = request.POST.get('origin', bill.origin)
        bill.total = unmask_money(request.POST['total'], currency) if request.POST.get('total') else bill.total
        bill.code = request.POST.get('code', bill.code)
        bill.link = request.POST.get('link', bill.link)
        bill.issue_date = issue_date if issue_date != '' else None
        bill.due_date = due_date if due_date != '' else None
        bill.paid_at = paid_at if paid_at != '' else None
        bill.invoice = request.POST.get('invoice', bill.invoice)
        bill.receipt = request.POST.get('receipt', bill.receipt)
        bill.authentication_key = request.POST.get('authentication_key', bill.authentication_key)
        bill.payment_info = request.POST.get('payment_info', bill.payment_info)

        bill.save()

        for file in request.FILES.getlist('proofs'):
            BillProof.objects.create(
                bill=bill,
                file=file,
            ).save()

    return process_filters(request, 'balance', slug)


def download_bill(request, slug, bill_id, proof_id):
    if not get_permission(request, 'view', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    file_name = Bill.objects.get(id=bill_id).proofs.get(id=proof_id).file.name
    file_content = default_storage.open(file_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'
    return response


def change_status(request, slug, bill_id):
    if not get_permission(request, 'change', 'bill'):
        return render(request, 'home/page-404.html')

    bill = Bill.objects.get(id=bill_id)
    reconcile = request.POST.get('reconcile', False)

    if not bill.paid:
        bill.paid_at = request.POST.get('bill_paid_at', datetime.now())
        bill.invoice = request.POST.get('invoice', None)
        bill.receipt = request.POST.get('receipt', None)
        bill.authentication_key = request.POST.get('authentication_key', None)
        bill.payment_info = request.POST.get('payment_info', '')
        bill.paid = True
        if bill.installments_number > 1:
            for installment in bill.installments.filter(paid=False):
                installment.paid = True
                installment.paid_at = bill.paid_at
                installment.save()

    else:
        bill.paid = False
        bill.payment_info = ''
        if bill.installments_number > 1:
            for installment in bill.installments.filter(paid=True, paid_at=bill.paid_at):
                installment.paid = False
                installment.paid_at = None
                installment.save()

        bill.paid_at = None

    if reconcile:
        bill.reconciled = True

    bill.save()

    if request.POST.get('client_page', False):
        return redirect('client_details', slug=slug)

    return process_filters(request, 'balance', slug)


def sort_and_filter_bills(request, slug):
    return process_filters(
        request, 'balance', slug,
        order='asc' if request.POST.get('asc', None) else 'desc'
    )


def filter_bill_objects(filters, slug):
    bills = Bill.objects.filter(client=Client.objects.get(slug=slug))

    if filters is not None:
        filters_list = filters.split('&')

        office, method, category, payer, origin, installments, code = ['all'] * 7
        from_date, to_date = [False] * 2
        late, paid, pending = [True] * 3
        min_value, max_value = [None] * 2

        for item in filters_list:
            payer = item.split('=')[1] if item.startswith('payer') else payer
            office = item.split('=')[1] if item.startswith('office') else office
            from_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('from') else from_date
            to_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            method = item.split('=')[1] if item.startswith('method') else method
            category = item.split('=')[1] if item.startswith('category') else category
            origin = item.split('=')[1] if item.startswith('origin') else origin
            installments = item.split('=')[1] if item.startswith('installments') else installments
            code = item.split('=')[1] if item.startswith('code') else code
            late = item.split('=')[1] if item.startswith('late') else late
            paid = item.split('=')[1] if item.startswith('paid') else paid
            pending = item.split('=')[1] if item.startswith('pending') else pending
            min_value = item.split('=')[1] if item.startswith('value_min') else min_value
            max_value = item.split('=')[1] if item.startswith('value_max') else max_value

        if payer != 'all':
            bills = bills.filter(payer__id=int(payer))

        if office != 'all':
            bills = bills.filter(office__id=int(office))

        if from_date and to_date and from_date < to_date:
            bills = bills.filter(due_date__gte=from_date, due_date__lte=to_date)
        elif from_date:
            bills = bills.filter(due_date__gte=from_date)
        elif to_date:
            bills = bills.filter(due_date__lte=to_date)

        if method != 'all':
            bills = bills.filter(method=method.replace('-', ' ').capitalize())

        if category != 'all':
            if category == 'income':
                bills = bills.filter(category__in=INCOME_CATEGORIES)
            elif category == 'expense':
                bills = bills.filter(category__in=EXPENSE_CATEGORIES)
            else:
                bills = bills.filter(category=category)

        if origin != 'all':
            bills = bills.filter(origin=origin)

        if code != 'all':
            match code:
                case 'code':
                    bills = bills.filter(Q(code__isnull=False) & ~Q(code=''))
                case 'link':
                    bills = bills.filter(Q(link__isnull=False) & ~Q(link=''))
                case 'both':
                    bills = bills.filter(
                        Q(code__isnull=False) & ~Q(code='') & Q(link__isnull=False) & ~Q(link='')
                    )
                case _:
                    pass

        if late == 'false':
            bills = bills.filter(late=False)

        if paid == 'false':
            bills = bills.filter(paid=False)

        if pending == 'false':
            bills = bills.filter(Q(paid=True, late=False) | Q(paid=False, late=True))

        if min_value:
            bills = bills.filter(total__gte=min_value)

        if max_value:
            bills = bills.filter(total__lte=max_value)

        if installments != 'all':
            if installments == 'true':
                bills = bills.filter(installments_number__gte=1)
            else:
                bills = bills.filter(installments_number__lt=1)

    return bills, bills.order_by('-id').first().id if bills.count() > 0 else 0


def filter_bills(request, slug):
    universal_min_value = str(Bill.objects.all().order_by('total').first().total).replace(
        '$' if request.POST.get('currency', 'BRL') == 'USD' else 'R$' if request.POST.get('currency',
                                                                                          'BRL') == 'BRL' else '€',
        '').replace(',', '') if Bill.objects.all().count() > 0 else 0
    universal_max_value = str(Bill.objects.all().order_by('-total').first().total).replace(
        '$' if request.POST.get('currency', 'BRL') == 'USD' else 'R$' if request.POST.get('currency',
                                                                                          'BRL') == 'BRL' else '€',
        '').replace(',', '') if Bill.objects.all().count() > 0 else 0

    payer = request.POST['payer']
    office = request.POST['office']
    from_date = request.POST['from']
    to_date = request.POST['to']
    category = request.POST['category']
    origin = request.POST['origin']
    method = request.POST['method']
    installments = request.POST['installments']
    code = request.POST['code']
    late = request.POST.get('late_filter', 'false')
    paid = request.POST.get('paid_filter', 'false')
    pending = request.POST.get('pending_filter', 'false')
    min_value = request.POST['range_value_low']
    max_value = request.POST['range_value_high']

    filter_list = [
        f'payer={payer}' if payer else '%',
        f'office={office}' if office else '%',
        f'from={from_date}' if from_date and from_date != to_date else '%',
        f'to={to_date}' if to_date and from_date != to_date else '%',
        f'method={method}' if method else '%',
        f'category={category}' if category else '%',
        f'origin={origin}' if origin else '%',
        f'installments={installments}' if installments else '%',
        f'code={code}' if code else '%',
        f'late={late}' if late == 'false' else '%',
        f'paid={paid}' if paid == 'false' else '%',
        f'pending={pending}' if pending == 'false' else '%',
        f'value_min={min_value}' if min_value and min_value != universal_min_value else '%',
        f'value_max={max_value}' if max_value and max_value != universal_max_value else '%',
    ]

    # Convert the list to a string with appropriate format, avoiding empty values
    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    return process_filters(request, 'balance', slug, filter_string)


############################################


def upload_proofs(request, slug):
    if not get_permission(request, 'add', 'billproof'):
        return render(request, 'home/page-404.html')

    if request.method == "POST" and request.FILES:
        files = request.FILES.getlist('proofs')
        for file in files:
            BillProof.objects.create(
                file=file,
                bill=Bill.objects.get(id=request.POST['bill_id'])
            )

        sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
        sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
        filters = request.POST.get('filters', 'None')

        if sorted_by != '' and filters != 'None':
            return redirect('sorted_filtered_client_balance', slug=slug,
                            sorted_by=sorted_by, sort_type=sort_type, filters=filters)
        if sorted_by not in ['', 'None']:
            return redirect('sorted_client_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
        elif filters != 'None':
            return redirect('filtered_client_balance', slug=slug, filters=filters)
        else:
            return redirect('client_balance', slug=slug)

    return redirect('client_balance', slug=slug)


def delete_proof(request, slug, proof_id):
    if not get_permission(request, 'delete', 'billproof'):
        return render(request, 'home/page-404.html')

    proof = BillProof.objects.get(id=proof_id)
    proof.delete()

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_client_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_client_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_client_balance', slug=slug, filters=filters)
    else:
        return redirect('client_balance', slug=slug)


############################################


def installment_change_status(request, slug, bill_id, installment_id):
    if not get_permission(request, 'change', 'bill'):
        return render(request, 'home/page-404.html')

    current = BillInstallment.objects.get(id=installment_id)

    if not current.paid:
        current.paid_at = request.POST.get('bill_paid_at', datetime.now())
    else:
        current.paid_at = None

    current.paid = not current.paid
    current.invoice = request.POST.get('invoice', None)
    current.receipt = request.POST.get('receipt', None)
    current.authentication_key = request.POST.get('authentication_key', None)
    current.payment_info = request.POST.get('installment_info', current.payment_info)
    current.save()

    installments = BillInstallment.objects.filter(bill__id=bill_id).order_by('due_date')
    unpaid = installments.filter(paid=False)

    if unpaid.count() > 0:
        current.bill.due_date = unpaid[0].due_date
        if current.bill.paid:
            current.bill.paid = False
            current.bill.paid_at = current.paid_at
            current.bill.save()

    else:
        current.bill.paid = True
        current.bill.paid_at = installments.last().paid_at
        current.bill.save()

    current.bill.save()

    if request.POST.get('client_page', False):
        return redirect('client_details', slug=slug)

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_client_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_client_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_client_balance', slug=slug, filters=filters)
    else:
        return redirect('client_balance', slug=slug)


def installment_edit(request, slug, bill_id, installment_id):
    if not get_permission(request, 'change', 'bill'):
        return render(request, 'home/page-404.html')

    currency = request.POST.get('currency', 'BRL')

    installment = BillInstallment.objects.get(id=installment_id)
    bill = Bill.objects.get(id=bill_id)

    new_installment_value = unmask_money(request.POST.get('installment_value', 0), currency)
    due_date = request.POST.get('installment_due_date', installment.due_date)

    installment.value = new_installment_value
    installment.due_date = due_date if due_date != '' else None
    installment.invoice = request.POST.get('invoice', installment.invoice)
    installment.receipt = request.POST.get('receipt', installment.receipt)
    installment.authentication_key = request.POST.get('authentication_key', installment.authentication_key)
    installment.payment_info = request.POST.get('installment_info', installment.payment_info)
    installment.save()

    if installment.due_date is None:
        try:
            installment.bill.due_date = installment.bill.installments.filter(
                paid=False, due_date__isnull=False).order_by('due_date').first().due_date
        except AttributeError:
            try:
                installment.bill.due_date = installment.bill.installments.filter(paid=False).order_by('due_date').last().due_date
            except AttributeError:
                installment.bill.due_date = installment.bill.installments.order_by('due_date').last().due_date

        installment.bill.save()

    elif bill.due_date is None or BillInstallment.objects.get(id=installment_id).due_date < bill.due_date:
        bill.due_date = due_date if due_date != '' else None
        bill.save()

    return process_filters(request, 'balance', slug)


def installments_edit_all(request, slug, bill_id):
    if not get_permission(request, 'change', 'bill'):
        return render(request, 'home/page-404.html')

    currency = request.POST.get('currency', 'BRL')

    values = {key: value for key, value in request.POST.items() if key.startswith('installment_value')}
    due_dates = {key: value for key, value in request.POST.items() if key.startswith('installment_due_date')}

    for value, due_date in zip(values.items(), due_dates.items()):
        installment_id = value[0].split('_')[2]
        value = unmask_money(value[1], currency)
        due_date = due_date[1] if due_date[1] != '' else None
        installment = BillInstallment.objects.get(id=installment_id)

        if (Money(value, currency=currency) != installment.value or
                datetime.strptime(due_date, '%Y-%m-%d').date() != installment.due_date):

            installment.value = value
            installment.due_date = due_date
            installment.save()

    return process_filters(request, 'balance', slug)


def installment_delete(request, slug, bill_id, installment_id):
    if not get_permission(request, 'change', 'bill'):
        return render(request, 'home/page-404.html')

    installment = BillInstallment.objects.get(id=installment_id)
    installment.delete()

    ordered_installments = installment.bill.installments.all().order_by('due_date')
    unpaid = ordered_installments.filter(paid=False)
    if unpaid.count() >= 1:
        installment.bill.due_date = unpaid.first().due_date
    else:
        installment.bill.due_date = ordered_installments.last().due_date

    installment.bill.save()

    for i, installment in enumerate(ordered_installments):
        installment.partial_id = i + 1
        installment.save()

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_client_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_client_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_client_balance', slug=slug, filters=filters)
    else:
        return redirect('client_balance', slug=slug)
