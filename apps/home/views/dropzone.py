from django.shortcuts import render, redirect
from apps.home.models import BillProof, Bill
from django.http import JsonResponse


def home(request):
    context = {
        'objects': BillProof.objects.all()
    }
    return render(request, "home/dropzone.html", context)


def upload_proofs(request):
    if request.method == "POST" and request.FILES:
        files = request.FILES
        for f in files:
            file = files.get(f)

            proof = BillProof.objects.create(file=file, token=request.POST.get('token'))
            proof.save()

        return JsonResponse({'message': 'Upload successful'})

    return JsonResponse({'message': 'Invalid request'}, status=400)


def create_object(request):
    if request.method == "POST":
        token = request.POST.get('csrfmiddlewaretoken')
        bill = Bill(
            title=token,
            created_by=request.user
        )
        bill.save()

        for proof in BillProof.objects.filter(token=token):
            proof.bill = bill
            proof.save()

    return redirect('dropzone')


def delete_object(request, id):
    bill = BillProof.objects.get(id=id)
    bill.delete()

    return redirect('dropzone')

