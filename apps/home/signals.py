from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from .models import BillInstallment, Bill


@receiver(post_save, sender=BillInstallment)
def update_total_bill(sender, instance, created, **kwargs):
    bill = instance.bill
    bill_installments = bill.installments.all()

    if created:
        bill.total += instance.value
        bill.save()
    else:
        bill.total = sum([inst.value for inst in bill_installments])
        bill.partial = sum([inst.value for inst in bill_installments if inst.paid])
        bill.save()


@receiver(post_delete, sender=BillInstallment)
def update_total_bill_on_delete(sender, instance, **kwargs):
    bill = instance.bill

    bill_installments = bill.installments.all()
    bill.installments_number = bill_installments.count()
    bill.total = sum([inst.value for inst in bill_installments])

    if instance.paid:
        bill.partial = sum([inst.value for inst in bill_installments if inst.paid])

    bill.save()


@receiver(post_save, sender=Bill)
def check_due_date(sender, instance, created, **kwargs):
    if not created and instance.installments.count() > 0:
        bill_installments = instance.installments.order_by('due_date')
        unpaid_installments = bill_installments.filter(paid=False)
        last_installment = bill_installments.last()

        if instance.due_date != last_installment.due_date and instance.due_date != unpaid_installments.first().due_date:
            if unpaid_installments.exists():
                instance.due_date = unpaid_installments.first().due_date
            else:
                instance.due_date = last_installment.due_date

            instance.save()
        else:
            return

