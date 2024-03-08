import os
from datetime import datetime
from django.db.models import Q
from django.http import HttpResponse
from django.shortcuts import render, redirect
from apps.home.models import Project, Profile, Office, Bill, Client, unmask_money


def get_permission(request, permission_type, model='bill'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def check_late_bills():
    late_bills = Bill.objects.filter(Q(due_date__lt=datetime.now().date()) & Q(paid=False))
    unlate_bills = Bill.objects.filter(Q(due_date__gte=datetime.now().date()) & Q(paid=False) & Q(late=True))
    for bill in late_bills:
        bill.save()

    for bill in unlate_bills:
        bill.late = False
        bill.save()


def filter_options(value):
    correlation = {
        'int-earn': 'Interest earned',
        'cap-pay': 'Capital payment',
        'inc-inv': 'Income investment',
        'eq-sales': 'Equipment sales',
        'credit': 'Credit card',
        'bank-exp': 'Bank',
        'maintenance-exp': 'Maintenance',
        'taxes-exp': 'Taxes',
        'eq-exp': 'Equipment',
        'staff-exp': 'Staff',
        'IOF/IR-on-applications': 'IOF/IR on applications',
    }

    if value in correlation.keys():
        return correlation[value]
    else:
        return value.replace('-', ' ').capitalize()


def filter_bill_objects(filters):
    bills = Bill.objects.all()

    if filters is not None:
        filters_list = filters.split('&')

        office, method, category, client = 'all', 'all', 'all', 'all'
        from_date, to_date = False, False
        late, paid, pending = True, True, True
        min_value, max_value = None, None

        for item in filters_list:
            office = item.split('=')[1] if item.startswith('office') else office
            from_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('from') else from_date
            to_date = datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            method = item.split('=')[1] if item.startswith('method') else method
            client = item.split('=')[1] if item.startswith('client') else client
            category = item.split('=')[1] if item.startswith('category') else category
            late = item.split('=')[1] if item.startswith('late') else late
            paid = item.split('=')[1] if item.startswith('paid') else paid
            pending = item.split('=')[1] if item.startswith('pending') else pending
            min_value = item.split('=')[1] if item.startswith('value_min') else min_value
            max_value = item.split('=')[1] if item.startswith('value_max') else max_value

            if office != 'all':
                bills = bills.filter(office__id=int(office))

            if from_date and to_date and from_date < to_date:
                bills = bills.filter(due_date__gte=from_date)
                bills = bills.filter(due_date__lte=to_date)
            elif from_date:
                bills = bills.filter(due_date__gte=from_date)
            elif to_date:
                bills = bills.filter(due_date__lte=to_date)

            if method != 'all':
                bills = bills.filter(method=method)

            if client != 'all':
                bills = bills.filter(client__id=client)

            if category != 'all':
                if category == 'income':
                    bills = bills.filter(income=True)
                elif category == 'expense':
                    bills = bills.filter(income=False)
                else:
                    bills = bills.filter(category=category)

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

    return bills, bills.order_by('-id').first().id if bills.count() > 0 else 0


def sort_bill_objects(bills, sorted_by, sort_type):
    if sorted_by is not None:
        sorted_by = sorted_by.replace('-', '_')

    if sorted_by == 'client':
        all_bills = sorted(bills, key=lambda bill: getattr(bill.client, 'name', ''))

    elif sorted_by == 'office':
        all_bills = sorted(bills, key=lambda bill: getattr(bill.office, 'name', ''))

    elif sorted_by == 'project':
        all_bills = sorted(bills, key=lambda bill: getattr(bill.project, 'title', ''))

    else:
        sorted_by = 'total' if sorted_by == 'value' else sorted_by
        sorted_by = 'created_at' if sorted_by is None else sorted_by
        all_bills = sorted(bills, key=lambda bill: getattr(bill, sorted_by, ''))

    if sort_type == 'desc':
        all_bills = reversed(all_bills)

    return all_bills


def home(request, sorted_by=None, sort_type=None, filters=None):
    if not get_permission(request, 'view', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    check_late_bills()

    currency = request.POST.get('currency', 'BRL')

    all_bills, max_id = filter_bill_objects(filters)

    bills_to_receive = all_bills.filter(income=True)
    bills_received = all_bills.filter(income=True, paid=True)
    bills_to_pay = all_bills.filter(income=False)
    bills_paid = all_bills.filter(income=False, paid=True)
    bills_pending = all_bills.filter(paid=False)
    bills_late = all_bills.filter(late=True)

    bills_to_receive_total = sum([bill.total for bill in bills_to_receive])
    bills_to_receive_pending_total = sum([bill.total for bill in bills_to_receive if not bill.paid])
    bills_to_receive_late_total = sum([bill.total for bill in bills_to_receive if bill.late])
    bills_received_total = sum([bill.total for bill in bills_received])
    bills_to_pay_total = sum([bill.total for bill in bills_to_pay])
    bills_to_pay_pending_total = sum([bill.total for bill in bills_to_pay if not bill.paid])
    bills_to_pay_late_total = sum([bill.total for bill in bills_to_pay if bill.late])
    bills_paid_total = sum([bill.total for bill in bills_paid])
    bills_pending_total = sum([bill.total for bill in bills_pending])
    bills_late_total = sum([bill.total for bill in bills_late])

    bills_to_receive_count = bills_to_receive.count()
    bills_received_count = bills_received.count()
    bills_to_pay_count = bills_to_pay.count()
    bills_paid_count = bills_paid.count()
    bills_pending_count = bills_pending.count()
    bills_late_count = bills_late.count()

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'offices': Office.objects.all(),
        'clients': Client.objects.all(),
        'bills_to_receive': bills_to_receive,
        'bills_to_pay': bills_to_pay,
        'received': bills_received_count,
        'received_value': bills_received_total,
        'paid': bills_paid_count,
        'paid_value': bills_paid_total,
        'to_receive': bills_to_receive_count,
        'to_receive_value': bills_to_receive_total,
        'to_receive_late_value': bills_to_receive_late_total,
        'to_receive_pending_value': bills_to_receive_pending_total,
        'to_pay': bills_to_pay_count,
        'to_pay_value': bills_to_pay_total,
        'to_pay_late_value': bills_to_pay_late_total,
        'to_pay_pending_value': bills_to_pay_pending_total,
        'pending': bills_pending_count,
        'pending_value': bills_pending_total,
        'late': bills_late_count,
        'late_value': bills_late_total,
        'currency': currency,
        'date_now': datetime.now().date(),
        'currency_symbol': '$' if currency == 'USD' else 'R$' if currency == 'BRL' else '€',
        'sorted_by': sorted_by.replace('-', '_') if sorted_by else None,
        'sort_type': sort_type.replace('-', '_') if sort_type else None,
        'filters': filters,
        'min_value': str(Bill.objects.all().order_by('total').first().total).replace(
            '$' if currency == 'USD' else 'R$' if currency == 'BRL' else '€', '').replace(',',
                                                                                          '') if Bill.objects.all().count() > 0 else 0,
        'max_value': str(Bill.objects.all().order_by('-total').first().total).replace(
            '$' if currency == 'USD' else 'R$' if currency == 'BRL' else '€', '').replace(',',
                                                                                          '') if Bill.objects.all().count() > 0 else 0,
        'segment': 'administrative',
    }

    context.update({'bills': sort_bill_objects(all_bills, sorted_by, sort_type), 'max_id': max_id})

    return render(request, 'home/bills.html', context)


def new_bill(request):
    if not get_permission(request, 'add', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        bill = Bill(
            # Foreign Keys
            project=Project.objects.get(id=request.POST['project_id']) if request.POST.get('project_id',
                                                                                           '') != '' else None,
            client=Client.objects.get(id=request.POST['client_id']) if request.POST.get('client_id',
                                                                                        '') != '' else None,
            office=Office.objects.get(id=request.POST['office_id']) if request.POST.get('office_id',
                                                                                        '') != '' else None,
            created_by=request.user,

            # Char Fields
            title=request.POST.get('title', ''),
            category=filter_options(request.POST.get('category', '')),
            subcategory=request.POST.get('subcategory', None),
            method=filter_options(request.POST.get('method', '')),

            # Date Fields
            due_date=request.POST.get('due_date', None) if request.POST.get('due_date', None) != '' else None,

            # Text Fields
            description=request.POST.get('description', ''),

            # Money Fields
            installments_value=unmask_money(request.POST.get('installments_value', ''), currency),
            fees=unmask_money(request.POST.get('fees', ''), currency),
            discount=unmask_money(request.POST.get('discount', ''), currency),
            total=unmask_money(request.POST.get('total', ''), currency),

            # Boolean Fields
            income=True if request.POST['income'] == 'true' else False,

            # Integer Fields
            installments=request.POST.get('installments', 0),

            # File Fields
            proof=request.FILES.get('proof', None),
        )

        bill.save()

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '' and sorted_by != 'None':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_bills', filters=filters)
    else:
        return redirect('balance_page')


def delete_bill(request, bill_id):
    if not get_permission(request, 'delete', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    if request.method == 'POST':
        bill = Bill.objects.get(id=bill_id)
        if bill.proof:
            os.remove(bill.proof.path)

        bill.delete()

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '' and sorted_by != 'None':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_bills', filters=filters)
    else:
        return redirect('balance_page')


def change_status(request, bill_id):
    if not get_permission(request, 'change', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    if not bill.paid:
        bill.paid = True
        bill.save(paid=True)
    else:
        bill.paid = False
        bill.save(paid=False)

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '' and sorted_by != 'None':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_bills', filters=filters)
    else:
        return redirect('balance_page')


def sort_and_filter_bills(request):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_bills', filters=filters)
    else:
        return redirect('balance_page')


def filter_bills(request):
    universal_min_value = str(Bill.objects.all().order_by('total').first().total).replace(
        '$' if request.POST.get('currency', 'BRL') == 'USD' else 'R$' if request.POST.get('currency',
                                                                                          'BRL') == 'BRL' else '€',
        '').replace(',', '') if Bill.objects.all().count() > 0 else 0
    universal_max_value = str(Bill.objects.all().order_by('-total').first().total).replace(
        '$' if request.POST.get('currency', 'BRL') == 'USD' else 'R$' if request.POST.get('currency',
                                                                                          'BRL') == 'BRL' else '€',
        '').replace(',', '') if Bill.objects.all().count() > 0 else 0

    office = request.POST['office']
    from_date = request.POST['start_date']
    to_date = request.POST['end_date']
    method = request.POST['method']
    client = request.POST['client']
    category = request.POST['category']
    late = request.POST.get('late_filter', 'false')
    paid = request.POST.get('paid_filter', 'false')
    pending = request.POST.get('pending_filter', 'false')
    min_value = request.POST['range_value_low']
    max_value = request.POST['range_value_high']

    filter_list = [
        f'office={office}' if office != 'all' else '%',
        f'from={from_date}' if from_date != '' and from_date != to_date else '%',
        f'to={to_date}' if to_date != '' and from_date != to_date else '%',
        f'method={method}' if method != 'all' else '%',
        f'client={client}' if client != 'all' else '%',
        f'category={category}' if category != 'all' else '%',
        f'late={late}' if late == 'false' else '%',
        f'paid={paid}' if paid == 'false' else '%',
        f'pending={pending}' if pending == 'false' else '%',
        f'value_min={min_value}' if min_value != '' and min_value != universal_min_value else '%',
        f'value_max={max_value}' if max_value != '' and max_value != universal_max_value else '%',
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
        return redirect('sorted_filtered_bills',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_bills',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'])
    elif filter_string == '%':
        return redirect('balance_page')
    else:
        return redirect('filtered_bills', filters=filter_string)


def download_bill(request, bill_id):
    if not get_permission(request, 'view', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    file_path = bill.proof.path
    with open(file_path, 'rb') as file:
        response = HttpResponse(file.read(), content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{bill.proof.name.split("/")[-1]}"'
        return response


def edit_bill(request, bill_id):
    if not get_permission(request, 'change', 'bill'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    bill = Bill.objects.get(id=bill_id)
    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        # bill.project = Project.objects.get(id=request.POST.get('project_id', bill.project.id))
        bill.client = Client.objects.get(id=request.POST['client_id']) if request.POST.get(
            'client_id') else bill.client if request.POST.get('client_id') != '' else None
        bill.office = Office.objects.get(id=request.POST['office_id']) if request.POST.get(
            'office_id') else bill.office if request.POST.get('office_id') != '' else None
        bill.title = request.POST.get('title', bill.title)
        bill.category = filter_options(request.POST['category']) if request.POST.get('category') else bill.category
        bill.method = filter_options(request.POST['method']) if request.POST.get('method') else bill.method
        bill.due_date = request.POST.get('due_date', bill.due_date)
        bill.description = request.POST.get('description', bill.description)
        bill.installments_value = unmask_money(request.POST['installments_value'], currency) if request.POST.get(
            'installments_value') else bill.installments_value
        bill.fees = unmask_money(request.POST['fees'], currency) if request.POST.get('fees') else bill.fees
        bill.discount = unmask_money(request.POST['discount'], currency) if request.POST.get(
            'discount') else bill.discount
        bill.total = unmask_money(request.POST['total'], currency) if request.POST.get('total') else bill.total
        bill.installments = request.POST.get('installments', 0)
        if request.FILES.get('proof') and request.FILES.get('proof') != bill.proof and bill.proof:
            os.remove(bill.proof.path)
            bill.proof = request.FILES['proof']
        else:
            bill.proof = request.FILES.get('proof', bill.proof)

        bill.save()

    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and sorted_by != 'None' and filters != 'None':
        return redirect('sorted_filtered_bills', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '' and sorted_by != 'None':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_bills', filters=filters)
    else:
        return redirect('balance_page')
