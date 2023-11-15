from itertools import chain
from django.shortcuts import render, redirect
from apps.home.models import Profile, Unit, BillToReceive, BillToPay, unmask_money


def home(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/balance.html', context)


def bills(request):
    context = {
        'user_profile': Profile.objects.get(user=request.user),
        'units': Unit.objects.all(),
        'bills_to_receive': BillToReceive.objects.all(),
        'bills_to_pay': BillToPay.objects.all(),
        'bills': sorted(
            chain(BillToReceive.objects.all(), BillToPay.objects.all()),
            key=lambda bill: bill.due_date
        )
    }

    return render(request, 'home/bills.html', context)


def new_bill(request, bill_type, redirect_to='balance_page'):
    if request.method == 'POST':

        currency = request.POST.get('currency', 'USD')

        if bill_type == 'income':
            bill = BillToReceive(
                title=request.POST['bill_name'],
                unit=Unit.objects.get(id=request.POST['bill_beneficiary']),
                category=request.POST['bill_category'],
                value=unmask_money(request.POST['bill_value'], currency),
                fees=unmask_money(request.POST['bill_fees'], currency),
                discount=unmask_money(request.POST['bill_discount'], currency),
                total=unmask_money(request.POST['bill_total'], currency),
                method=request.POST['bill_method'],
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
                category=request.POST['bill_pay_category'],
                sub_category=request.POST['bill_pay_sub_category'],
                value=unmask_money(request.POST['bill_pay_value'], currency),
                due_date=request.POST['bill_pay_date'],
                description=request.POST['bill_pay_description'],
                proof=request.FILES.get('bill_pay_proof', None),
            )

            bill.save()

    return redirect(redirect_to)
