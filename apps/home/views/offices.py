from apps.home.views.balance import INCOME_CATEGORIES, EXPENSE_CATEGORIES, unmask_money, check_late_bills
from django.shortcuts import render, redirect, get_object_or_404
from apps.home.models import Profile, Office, Document, Bill, Client, Branch, BillInstallment
from django.core.files.storage import default_storage
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F
from django.http import HttpResponse
from datetime import datetime
from datetime import timedelta
from djmoney.money import Money


def get_paginated_offices(request, order_by):
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


def filter_bill_objects(filters, bills):

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

    return bills


#############################################################


def home(request, order_by=None):
    if not request.user.has_perm('home.view_office'):
        return render(request, 'home/page-404.html')

    paginator, offices = get_paginated_offices(request, order_by=order_by)

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'offices': offices,
        'segment': 'administrative',
    }

    return render(request, 'home/offices/home.html', context)


def create(request):
    if not request.user.has_perm('home.add_office'):
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
    if not request.user.has_perm('home.delete_office'):
        return render(request, 'home/page-404.html')

    office = Office.objects.get(id=office_id)
    office.delete()

    return redirect('offices_home')


##############################################################


def details(request, slug):
    if not request.user.has_perm('home.change_office'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    office = Office.objects.get(slug=slug)

    query = Q(office=office) & (Q(paid=True) | Q(installments__paid=True))

    office_bills = Bill.objects.filter(query).distinct()

    income_bills = office_bills.filter(category__in=INCOME_CATEGORIES)
    expense_bills = office_bills.filter(category__in=EXPENSE_CATEGORIES)
    total_income = sum([bill.partial for bill in income_bills])
    total_expense = sum([bill.partial for bill in expense_bills])

    last_month_bills = office_bills.filter(
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
        office=office, paid=False, due_date__lt=datetime.now().date() + timedelta(days=40)
    ).order_by('due_date')

    context = {
        'currency': 'BRL',  # TODO: Change to currency variable when implemented
        'office': office,
        'user_profile': Profile.objects.get(user=request.user),
        'segment': 'offices',
        'collaborators': Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(
            user__username__startswith='admin').exclude(user__username__startswith='hub'),
        'income_categories': INCOME_CATEGORIES,
        'expense_categories': EXPENSE_CATEGORIES,
        'bills_in_progress': bills_in_progress,
        'balance': total_income - total_expense,
        'income_percentage': round(income_percentage),
        'expense_percentage': round(expense_percentage),
        'last_month_balance': last_month_balance,
        'last_month_balance_percentage': round(last_month_percentage, 1),
        'clients': Client.objects.all(),
    }

    return render(request, 'home/offices/details.html', context)


def edit(request, slug):
    if not request.user.has_perm('home.change_office'):
        return render(request, 'home/page-404.html')

    office = Office.objects.get(slug=slug)

    if request.method == 'POST':
        office.name = request.POST.get('name', office.name)
        office.cnpj = request.POST.get('cnpj', office.cnpj)
        office.description = request.POST.get('about', office.description)
        office.location = request.POST.get('address', office.location)

        if request.FILES.get('avatar', None):
            if office.avatar:
                office.avatar.delete(save=False)

            office.avatar = request.FILES['avatar']

        office.save()

    return redirect('office_details', slug=slug)


##############################################################


def balance(request, slug, sorted_by=None, sort_type=None, filters=None):
    if not request.user.has_perm('home.add_bill'):
        return render(request, 'home/page-404.html')

    check_late_bills()

    office = Office.objects.get(slug=slug)
    bills = filter_bill_objects(filters, Bill.objects.filter(office=office))

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
        'office': office,
        'bills': bills,
        'user_profile': Profile.objects.get(user=request.user),
        'segment': 'offices',
        'income_categories': INCOME_CATEGORIES,
        'expense_categories': EXPENSE_CATEGORIES,
        'received': sum([bill.partial for bill in income_bills]),
        'income': sum([bill.total for bill in income_bills]),
        'paid': sum([bill.partial for bill in expense_bills]),
        'expense': sum([bill.total for bill in expense_bills]),
        'pending_income': pending_income,
        'late_income': late_income,
        'pending_expense': pending_expense,
        'late_expense': late_expense,
        'clients': Client.objects.all(),
        'sorted_by': sorted_by,
        'sort_type': sort_type,
        'filters': filters,
        'min_value': str(bills.order_by('total').first().total)[2:].replace(',', '') if bills.count() > 0 else 0,
        'max_value': str(bills.order_by('-total').first().total)[2:].replace(',', '') if bills.count() > 0 else 0,
    }

    return render(request, 'home/offices/balance.html', context)


def new_bill(request, slug):
    if not request.user.has_perm('home.add_bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        bill = Bill(
            # Foreign Keys
            client=Client.objects.get(id=request.POST['client_id']) if request.POST.get('client_id') != '' else None,
            payer=Branch.objects.get(id=request.POST['payer_id']) if request.POST.get('payer_id') != '' else None,
            office=Office.objects.get(slug=slug),
            created_by=request.user,
            # Char Fields
            title=request.POST.get('title', ''),
            category=request.POST.get('category', ''),
            method=request.POST.get('method', ''),
            origin=request.POST.get('origin', ''),
            code=request.POST.get('code', ''),
            # Date Fields
            due_date=request.POST.get('due_date', None) if request.POST.get('due_date', None) != '' else None,
            # Money Fields
            total=unmask_money(request.POST.get('total', ''), currency),
            # Integer Fields
            installments_number=request.POST.get('installments', 0),
            # File Fields
            proof=request.FILES.get('proof', None),
            # URL Fields
            link=request.POST.get('link', None),
        )

        status = request.POST.get('status', 'Pending')
        if 'Paid' in status:
            bill.paid = True
            bill.paid_at = datetime.now()

        if 'reconciled' in status:
            bill.reconciled = True

        bill.save()

        if int(request.POST.get('installments', 1)) > 1 and request.POST.get('installments_value'):
            installments = request.POST.get('installments')
            installments_value = unmask_money(request.POST.get('installments_value', ''), currency)
            bill.installments_frequency = request.POST.get('installments_frequency', 0)
            if bill.installments_frequency == '':
                bill.installments_frequency = 0

            for i in range(1, int(installments) + 1):
                installment = BillInstallment(
                    bill=bill,
                    partial_id=i,
                    value=installments_value,
                    due_date=datetime.strptime(
                        str(bill.due_date), "%Y-%m-%d"
                    ) + timedelta(days=int(bill.installments_frequency) * (i - 1)) if bill.due_date else None,
                )
                installment.save()

            bill.save()

        else:
            bill.installments_number = 0
            bill.installments_frequency = 0
            bill.save()

        sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
        sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
        filters = request.POST.get('filters', 'None')

        if sorted_by != '' and filters != 'None':
            return redirect('sorted_filtered_office_balance', slug=slug,
                            sorted_by=sorted_by, sort_type=sort_type, filters=filters)
        if sorted_by not in ['', 'None']:
            return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
        elif filters != 'None':
            return redirect('filtered_office_balance', slug=slug, filters=filters)
        else:
            return redirect('office_balance', slug=slug)

    return redirect('office_balance', slug=slug)


def delete_bill(request, slug, bill_id):
    if not request.user.has_perm('home.delete_bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    file = bill.proof
    if file:
        file.delete(save=False)

    bill.delete()

    if request.POST.get('office_page', False):
        return redirect('office_details', slug=slug)

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


def edit_bill(request, slug, bill_id):
    if not request.user.has_perm('home.change_bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    if request.method == 'POST':
        due_date = request.POST.get('due_date', bill.due_date)
        currency = request.POST.get('currency', 'USD')
        bill.client = Client.objects.get(slug=request.POST['client_slug'])
        bill.payer = Branch.objects.get(id=request.POST['payer_id']) if request.POST.get(
            'payer_id') else bill.payer if request.POST.get('payer_id') != '' else None
        bill.office = Office.objects.get(id=request.POST['office_id']) if request.POST.get(
            'office_id') else bill.office if request.POST.get('office_id') != '' else None
        bill.title = request.POST.get('title', bill.title)
        bill.category = request.POST.get('category', bill.category)
        bill.method = request.POST.get('method', bill.method)
        bill.origin = request.POST.get('origin', bill.origin)
        bill.due_date = due_date if due_date != '' else None
        bill.total = unmask_money(request.POST['total'], currency) if request.POST.get('total') else bill.total
        bill.code = request.POST.get('code', bill.code)
        bill.link = request.POST.get('link', bill.link)
        bill.payment_info = request.POST.get('payment_info', bill.payment_info)

        installments_number_from_form = int(request.POST.get('installments', 0))
        installments_value_from_form = unmask_money(request.POST.get('installments_value', ''), currency)
        installments_frequency_from_form = request.POST.get('installments_frequency', 30)

        num_change = [
            installments_number_from_form != bill.installments_number,
            installments_number_from_form > 1,
            installments_value_from_form > 0,
        ]

        val_change = [
            installments_value_from_form != bill.installments.filter(paid=False).first(
            ).value if bill.installments.filter(paid=False) else False,
            installments_value_from_form > 0,
        ]

        freq_change = [
            installments_frequency_from_form != bill.installments_frequency,
            installments_value_from_form > 0,
        ]

        if all(freq_change) and bill.due_date is not None:
            bill.installments_frequency = installments_frequency_from_form
            for installment in bill.installments.all():
                installment.due_date = datetime.strptime(
                    str(bill.due_date), "%Y-%m-%d"
                ) + timedelta(days=int(installments_frequency_from_form) * (installment.partial_id - 1))
                installment.save()

        if all(num_change):
            installments = BillInstallment.objects.filter(bill=bill)
            installments.delete()
            bill.installments_number = installments_number_from_form
            for i in range(1, installments_number_from_form + 1):
                installment = BillInstallment(
                    bill=bill,
                    partial_id=i,
                    value=installments_value_from_form,
                    due_date=datetime.strptime(
                        str(bill.due_date), "%Y-%m-%d"
                    ) + timedelta(days=int(bill.installments_frequency) * (i - 1)) if bill.due_date else None,
                )
                installment.save()

        elif num_change[0] and not num_change[1]:
            installments = BillInstallment.objects.filter(bill=bill)
            installments.delete()
            bill.installments_number = 0
            bill.installments_frequency = 0

        elif not num_change[0] and all(val_change):
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

        if request.POST.get('office_page', False):
            return redirect('office_details', slug=slug)

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


def download_bill(request, slug, bill_id):
    if not request.user.has_perm('home.view_bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    file_name = bill.proof.name
    file_content = default_storage.open(file_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'
    return response


def change_status(request, slug, bill_id):
    if not request.user.has_perm('home.change_bill'):
        return render(request, 'home/page-404.html')

    bill = Bill.objects.get(id=bill_id)
    reconcile = request.POST.get('reconcile', False)

    if not bill.paid:
        bill.paid_at = request.POST.get('bill_paid_at', datetime.now())
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

    if request.POST.get('office_page', False):
        return redirect('office_details', slug=slug)

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


def sort_and_filter_bills(request, slug):
    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


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

    if request.POST['sort_by'] != 'None' and filter_string != '%':
        return redirect('sorted_filtered_office_balance',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string, slug=slug)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_office_balance',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'], slug=slug)
    elif filter_string == '%':
        return redirect('office_balance', slug=slug)
    else:
        return redirect('filtered_office_balance', filters=filter_string, slug=slug)


############################################


def installment_change_status(request, slug, bill_id, installment_id):
    if not request.user.has_perm('home.change_bill'):
        return render(request, 'home/page-404.html')

    current = BillInstallment.objects.get(id=installment_id)

    if not current.paid:
        current.paid_at = request.POST.get('bill_paid_at', datetime.now())
    else:
        current.paid_at = None

    current.paid = not current.paid
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

    if request.POST.get('office_page', False):
        return redirect('office_details', slug=slug)

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


def installment_edit(request, slug, bill_id, installment_id):
    if not request.user.has_perm('home.change_bill'):
        return render(request, 'home/page-404.html')

    currency = request.POST.get('currency', 'BRL')

    current = BillInstallment.objects.get(id=installment_id)
    bill = Bill.objects.get(id=bill_id)

    prev_installment_value = current.value if current.value else 0
    new_installment_value = unmask_money(request.POST.get('installment_value', 0), currency)
    due_date = request.POST.get('installment_due_date', current.due_date)
    installment_payment_info = request.POST.get('installment_info', current.payment_info)

    current.value = new_installment_value
    current.due_date = due_date if due_date != '' else None
    current.payment_info = installment_payment_info
    current.save()

    if prev_installment_value != new_installment_value:
        bill.total -= prev_installment_value
        bill.total += Money(new_installment_value, currency=bill.total.currency)
        bill.save()

    if current.due_date is None:
        try:
            current.bill.due_date = current.bill.installments.filter(
                paid=False, due_date__isnull=False).order_by('due_date').first().due_date
        except AttributeError:
            try:
                current.bill.due_date = current.bill.installments.filter(paid=False).order_by('due_date').last().due_date
            except AttributeError:
                current.bill.due_date = current.bill.installments.order_by('due_date').last().due_date

        current.bill.save()

    elif bill.due_date is None or BillInstallment.objects.get(id=installment_id).due_date < bill.due_date:
        bill.due_date = due_date if due_date != '' else None
        bill.save()

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


def installment_delete(request, slug, bill_id, installment_id):
    if not request.user.has_perm('home.change_bill'):
        return render(request, 'home/page-404.html')

    installment = BillInstallment.objects.get(id=installment_id)

    installment.bill.total -= installment.value
    installment.bill.installments_number -= 1
    installment.bill.due_date = installment.bill.installments.filter(paid=False).order_by('due_date').first().due_date
    if installment.paid:
        installment.bill.partial -= installment.value

    installment.delete()

    if installment.bill.installments_number == 1:
        installment.bill.installments_number = 0

    last_due_date = installment.bill.installments.all().order_by('due_date')
    if last_due_date.filter(paid=False).count() >= 1:
        installment.bill.due_date = last_due_date.filter(paid=False).first().due_date
    else:
        installment.bill.due_date = last_due_date.last().due_date

    installment.bill.save()

    for i, installment in enumerate(BillInstallment.objects.filter(bill__id=bill_id).order_by('due_date')):
        installment.partial_id = i + 1
        installment.save()

    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = request.POST.get('sort_type', None) if request.POST.get('sort_type', None) != 'None' else None
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_office_balance', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    if sorted_by not in ['', 'None']:
        return redirect('sorted_office_balance', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_balance', slug=slug, filters=filters)
    else:
        return redirect('office_balance', slug=slug)


##############################################################


def documents(request, slug, sorted_by=None, sort_type=None, filters=None):
    if not request.user.has_perm('home.add_document'):
        return render(request, 'home/page-404.html')

    check_expired_documents()

    office = Office.objects.get(slug=slug)
    documents = filter_documents_objects(filters, slug)[0]

    if sorted_by is not None:
        documents = documents.order_by(
            f'{"-" if sort_type == "desc" else ""}{sorted_by}'
        )

    context = {
        'office': office,
        'user_profile': Profile.objects.get(user=request.user),
        'segment': 'offices',
        'documents': documents,
        'filters': filters,
        'sorted_by': sorted_by,
        'sort_type': sort_type,
    }

    return render(request, 'home/offices/documents.html', context)


def new_document(request, slug, document_id=None):
    if not request.user.has_perm('home.add_document'):
        return render(request, 'home/page-404.html')

    office = Office.objects.get(slug=slug)

    if request.method == 'POST':
        expiration = request.POST.get('expiration', None)

        if document_id:
            document = Document.objects.get(id=document_id)
            document.name = request.POST.get('name')
            document.expiration = expiration if expiration else None
            document.category = request.POST.get('category', document.category)
            document.description = request.POST.get('description', document.description)

        else:
            document = Document(
                office=office,
                name=request.POST.get('name'),
                expiration=expiration if expiration else None,
                category=request.POST.get('category'),
                description=request.POST.get('description'),
                file=request.FILES['file'],
                uploaded_by=request.user,
            )

        document.save()

    return redirect('office_documents', slug=slug)


def delete_document(request, slug, document_id):
    if not request.user.has_perm('home.delete_document'):
        return render(request, 'home/page-404.html')

    document = Document.objects.get(id=document_id)

    if document.file:
        document.file.delete(save=False)

    document.delete()

    return redirect('office_documents', slug=slug)


def download_document(request, slug, document_id):
    if not request.user.has_perm('home.view_document'):
        return render(request, 'home/page-404.html')

    document = get_object_or_404(Document, id=document_id)

    document_name = document.file.name
    file_content = default_storage.open(document_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document_name.split("/")[-1]}"'
    return response


def sort_and_filter_documents(request, slug):
    sorted_by = request.POST['sort_by'] if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by not in ['', 'None'] and filters != 'None':
        return redirect('sorted_filtered_office_documents', slug=slug,
                        sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by not in ['', 'None']:
        return redirect('sorted_office_documents', slug=slug, sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_office_documents', slug=slug, filters=filters)
    else:
        return redirect('office_documents', slug=slug)


def filter_documents_objects(filters, slug):
    documents = Document.objects.filter(office=Office.objects.get(slug=slug))

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

    filter_list = [
        f'from={from_date}' if from_date != '' and from_date != to_date else '%',
        f'to={to_date}' if to_date != '' and from_date != to_date else '%',
        f'category={category}' if category != 'all' else '%',
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

    if request.POST['sort_by'] != 'None' and filter_string != '%':
        return redirect('sorted_filtered_office_documents', slug=slug,
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_office_documents', slug=slug,
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'])
    elif filter_string == '%':
        return redirect('office_documents', slug=slug)
    else:
        return redirect('filtered_office_documents', filters=filter_string, slug=slug)

