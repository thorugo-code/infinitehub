import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from apps.home.models import Profile, Equipments
from django.core.paginator import Paginator
from django.core.files.storage import default_storage


def get_paginated_equipments(request):
    equipments_list = Equipments.objects.all()
    paginator = Paginator(equipments_list, 6)  # Show 6 projects per page
    page = request.GET.get('page')
    equipments = paginator.get_page(page)
    return paginator, equipments


def inventory_list(request):

    if request.method == 'POST':
        name = request.POST.get('name', 'Untitled')
        series = request.POST.get('series', 'N/A')
        supplier = request.POST.get('supplier', 'Untitled')

        acquisition_date_str = request.POST.get('acquisition-date', datetime.datetime.now)
        acquisition_date = datetime.datetime.strptime(acquisition_date_str, '%Y-%m-%d').date()

        price_str = request.POST.get('equipment_value', 'USD 0.00').replace('USD ', '').replace(',', '')
        price = float(price_str) if price_str else 0

        description = request.POST.get('about', '')

        equipment = Equipments(
            name=name,
            series=series,
            supplier=supplier,
            acquisition_date=acquisition_date,
            price=price,
            description=description
        )
        equipment.save()

        return redirect('inventory_list')

    paginator, equipments = get_paginated_equipments(request)
    user_profile = Profile.objects.get(user=request.user)

    context = {
        'equipment_list': equipments,
        'user_profile': user_profile,
        'segment': 'inventory',
    }

    return render(request, 'home/inventory/equipments/home.html', context)


def download_qrcode_inventory(request, equipment_id):
    equipment = get_object_or_404(Equipments, pk=equipment_id)
    qrcode_name = equipment.qrcode.name
    file_content = default_storage.open(qrcode_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{qrcode_name.split("/")[-1]}"'
    return response


def delete_equipment(request, id):
    equipment = Equipments.objects.get(id=id)
    qrcode_path = equipment.qrcode
    qrcode_path.delete(save=False)
    equipment.delete()

    return redirect('inventory_list')
