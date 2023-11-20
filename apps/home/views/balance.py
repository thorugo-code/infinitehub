from datetime import datetime
from itertools import chain
from django.shortcuts import render, redirect
from apps.home.models import Profile, Unit, BillToReceive, BillToPay, Client, unmask_money
from django.db.models import Sum


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


def home(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'nearby_to_receive': BillToReceive.objects.filter(paid=False).order_by('due_date')[:8],
        'nearby_to_pay': BillToPay.objects.filter(paid=False).order_by('due_date')[:8],
        'date_now': datetime.now().date(),
    }

    return render(request, 'home/balance.html', context)


def bills(request):
    currency = request.POST.get('currency', 'USD')

    all_bills = sorted(
        chain(BillToReceive.objects.all(), BillToPay.objects.all()),
        key=lambda bill: bill.due_date
    )
    bills_to_receive = BillToReceive.objects.all()
    bills_received = BillToReceive.objects.filter(paid=True)
    bills_to_pay = BillToPay.objects.all()
    bills_paid = BillToPay.objects.filter(paid=True)
    bills_pending = chain(BillToReceive.objects.filter(paid=False), BillToPay.objects.filter(paid=False))
    bills_late = chain(BillToReceive.objects.filter(paid=False, due_date__lt=datetime.now().date()),
                       BillToPay.objects.filter(paid=False, due_date__lt=datetime.now().date()))

    bills_to_receive_total = sum([bill.total for bill in bills_to_receive])
    bills_received_total = sum([bill.total for bill in bills_received])
    bills_to_pay_total = sum([bill.value for bill in bills_to_pay])
    bills_paid_total = sum([bill.value for bill in bills_paid])
    bills_pending_total = sum([bill.total if bill in bills_to_receive else bill.value for bill in bills_pending])
    bills_late_total = sum([bill.total if bill in bills_to_receive else bill.value for bill in bills_late])

    bills_to_receive_count = bills_to_receive.count()
    bills_received_count = bills_received.count()
    bills_to_pay_count = bills_to_pay.count()
    bills_paid_count = bills_paid.count()
    bills_pending_count = len(
        list(chain(BillToReceive.objects.filter(paid=False), BillToPay.objects.filter(paid=False))))
    bills_late_count = len(list(chain(BillToReceive.objects.filter(paid=False, due_date__lt=datetime.now().date()),
                                      BillToPay.objects.filter(paid=False, due_date__lt=datetime.now().date()))))

    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'units': Unit.objects.all(),
        'clients': Client.objects.all(),
        'bills_to_receive': bills_to_receive,
        'bills_to_pay': bills_to_pay,
        'bills': all_bills,
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
        'currency_symbol': '$' if currency == 'USD' else 'R$',
    }

    return render(request, 'home/bills.html', context)


def new_bill(request, bill_type, redirect_to='balance_page'):
    if request.method == 'POST':

        currency = request.POST.get('currency', 'USD')

        if bill_type == 'income':
            bill = BillToReceive(
                title=request.POST['bill_name'],
                unit=Unit.objects.get(id=request.POST['bill_beneficiary']),
                category=filter_options(request.POST['bill_category']),
                client=Client.objects.get(id=request.POST['bill_receive_client']),
                value=unmask_money(request.POST['bill_value'], currency),
                fees=unmask_money(request.POST['bill_fees'], currency),
                discount=unmask_money(request.POST['bill_discount'], currency),
                total=unmask_money(request.POST['bill_total'], currency),
                method=filter_options(request.POST['bill_method']),
                due_date=request.POST['bill_due_date'],
                number_of_installments=request.POST.get('bill_installments_method', 0),
                value_of_installments=unmask_money(request.POST.get('bill_installments_value', ''), currency),
                description=request.POST['bill_description'],
                proof=request.FILES.get('bill_receive_proof', None),
            )

            bill.save()

        elif bill_type == 'expense':
            bill = BillToPay(
                title=request.POST['bill_name'],
                unit=Unit.objects.get(id=request.POST['bill_pay_local']),
                subcategory=filter_options(request.POST['bill_pay_category']),
                method=filter_options(request.POST['bill_pay_method']),
                value=unmask_money(request.POST['bill_pay_value'], currency),
                due_date=request.POST['bill_pay_date'],
                description=request.POST['bill_pay_description'],
                proof=request.FILES.get('bill_pay_proof', None),
            )

            bill.save()

    return redirect(redirect_to)


def delete_bill(request, bill_type, bill_id, redirect_to='balance_page'):
    if request.method == 'POST':

        if bill_type == 'income':
            bill = BillToReceive.objects.get(id=bill_id)
        else:
            bill = BillToPay.objects.get(id=bill_id)

        bill.delete()

    return redirect(redirect_to)


def set_as_paid(request, redirect_to='balance_page'):
    if request.method == 'POST':
        bill_id = request.POST['bill_id']
        bill_type = request.POST['bill_type']

        if bill_type == 'income':
            bill = BillToReceive.objects.get(id=bill_id)
        else:
            bill = BillToPay.objects.get(id=bill_id)

        bill.paid = True
        bill.save()

    return redirect(redirect_to)


def change_status(request, bill_type, bill_id, redirect_to='balance_page'):
    if request.method == 'POST':

        if bill_type == 'income':
            bill = BillToReceive.objects.get(id=bill_id)
        else:
            bill = BillToPay.objects.get(id=bill_id)

        bill.paid = not bill.paid
        bill.save()

    return redirect(redirect_to)
