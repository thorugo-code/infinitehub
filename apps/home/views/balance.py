from datetime import datetime
from django.shortcuts import render, redirect
from apps.home.models import Project, Profile, Office, Bill, Client, unmask_money


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
    }

    if value in correlation.keys():
        return correlation[value]
    else:
        return value.replace('-', ' ').capitalize()


def home(request, sorted_by=None, sort_type=None):
    currency = request.POST.get('currency', 'BRL')

    bills_to_receive = Bill.objects.filter(income=False)
    bills_received = Bill.objects.filter(income=False, paid=True)
    bills_to_pay = Bill.objects.filter(income=True)
    bills_paid = Bill.objects.filter(income=True, paid=True)
    bills_pending = Bill.objects.filter(paid=False)
    bills_late = Bill.objects.filter(late=True)

    bills_to_receive_total = sum([bill.total for bill in bills_to_receive])
    bills_received_total = sum([bill.total for bill in bills_received])
    bills_to_pay_total = sum([bill.total for bill in bills_to_pay])
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
        'to_pay': bills_to_pay_count,
        'to_pay_value': bills_to_pay_total,
        'pending': bills_pending_count,
        'pending_value': bills_pending_total,
        'late': bills_late_count,
        'late_value': bills_late_total,
        'currency': currency,
        'date_now': datetime.now().date(),
        'currency_symbol': '$' if currency == 'USD' else 'R$' if currency == 'BRL' else '€',
        'sorted_by': sorted_by.replace('-', '_') if sorted_by else None,
        'sort_type': sort_type.replace('-', '_') if sort_type else None,
    }

    if sorted_by == 'client':
        all_bills = sorted(Bill.objects.all(), key=lambda bill: getattr(bill.client, 'name'))

    elif sorted_by == 'office':
        all_bills = sorted(Bill.objects.all(), key=lambda bill: getattr(bill.office, 'name'))

    elif sorted_by == 'project':
        all_bills = sorted(Bill.objects.all(), key=lambda bill: getattr(bill.project, 'title'))

    else:
        sorted_by = 'total' if sorted_by == 'value' else sorted_by
        all_bills = sorted(Bill.objects.all(), key=lambda bill: getattr(bill, sorted_by))

    if sort_type == 'desc':
        all_bills = reversed(all_bills)

    context.update({'bills': all_bills})

    return render(request, 'home/bills.html', context)


def new_bill(request):

    if request.method == 'POST':
        currency = request.POST.get('currency', 'USD')
        bill = Bill(
            # Foreign Keys
            project=Project.objects.get(id=request.POST['project_id']) if request.POST.get('project_id', '') != '' else None,
            client=Client.objects.get(id=request.POST['client_id']) if request.POST.get('client_id', '') != '' else None,
            office=Office.objects.get(id=request.POST['office_id']) if request.POST.get('office_id', '') != '' else None,
            created_by=Profile.objects.get(user=request.user),

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

    return redirect('balance_page')


def delete_bill(request, bill_id):
    if request.method == 'POST':
        bill = Bill.objects.get(id=bill_id)
        bill.delete()

    return redirect('balance_page')


def change_status(request, bill_id):
    if request.method == 'POST':
        bill = Bill.objects.get(id=bill_id)
        bill.paid = not bill.paid
        bill.save()

    return redirect('balance_page')


def sort_bills(request):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'

    if sorted_by != '':
        return redirect('sorted_bills', sorted_by=sorted_by, sort_type=sort_type)

    return redirect('balance_page')
