from django import template
from django.db.models import Sum, Q
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template import loader
from django.urls import reverse
from django.views.decorators.http import require_POST
from apps.home.models import Project, UploadedFile, Profile, Equipments
from django.core.paginator import Paginator
import os


@login_required(login_url="/login/")
def index(request):
    context = {'segment': 'index',
               'user_profile': Profile.objects.get(user=request.user)}

    html_template = loader.get_template('home/index.html')
    return HttpResponse(html_template.render(context, request))


@login_required(login_url="/login/")
def pages(request):
    context = {}
    # All resource paths end in .html.
    # Pick out the html file name from the url. And load that template.
    try:
        user_profile = Profile.objects.get(user=request.user)
        context['user_profile'] = user_profile
    except Profile.DoesNotExist:
        pass

    try:

        load_template = request.path.split('/')[-1]

        if load_template == 'admin':
            return HttpResponseRedirect(reverse('admin:index'))
        context['segment'] = load_template

        html_template = loader.get_template('home/' + load_template)
        return HttpResponse(html_template.render(context, request))

    except template.TemplateDoesNotExist:

        html_template = loader.get_template('home/page-404.html')
        return HttpResponse(html_template.render(context, request))

    except:
        html_template = loader.get_template('home/page-500.html')
        return HttpResponse(html_template.render(context, request))


def get_paginated_files(request, category=None):
    if category is None:
        files_list = UploadedFile.objects.all()
    elif type(category) == str:
        files_list = UploadedFile.objects.filter(category=category)
    else:
        files_list = UploadedFile.objects.filter(category)

    paginator = Paginator(files_list, 6)  # Show 6 files per page
    page = request.GET.get('page')
    files = paginator.get_page(page)
    return paginator, files


def assets_list(request, category=None):
    user_profile = Profile.objects.get(user=request.user)

    if category == '3d-models':
        title = '3D Models'
        paginator, files = get_paginated_files(request, category)
    elif category == 'scripts':
        title = 'Scripts'
        paginator, files = get_paginated_files(request, category)
    elif category == 'unity':
        title = 'Unity'
        paginator, files = get_paginated_files(request, category)
    else:
        title = 'Others'
        category_filter = Q(category__in=['clouds', 'executable', 'folders', 'database',
                                          'office', 'images', 'video', 'others'])
        paginator, files = get_paginated_files(request, category_filter)

    return render(request, "home/assetsList.html", {'files_list': files,
                                                    'category': category,
                                                    'title': title,
                                                    'user_profile': user_profile})


def assets_hub(request):
    user_profile = Profile.objects.get(user=request.user)

    other_categories = ['clouds', 'executable', 'folders', 'database', 'office', 'images', 'video', 'others']

    category_filter = Q(category__in=other_categories)

    models_3d = UploadedFile.objects.filter(category='3d-models').count()
    scripts = UploadedFile.objects.filter(category='scripts').count()
    unity = UploadedFile.objects.filter(category='unity').count()
    others = UploadedFile.objects.filter(category_filter).count()

    values_3d = UploadedFile.objects.filter(category='3d-models').aggregate(Sum('value'))['value__sum']
    values_scripts = UploadedFile.objects.filter(category='scripts').aggregate(Sum('value'))['value__sum']
    values_unity = UploadedFile.objects.filter(category='unity').aggregate(Sum('value'))['value__sum']
    values_others = UploadedFile.objects.filter(category_filter).aggregate(Sum('value'))['value__sum']

    return render(request, "home/assetsPage.html", {'3d_models_files': models_3d,
                                                    'scripts_files': scripts,
                                                    'unity_files': unity,
                                                    'others_files': others,
                                                    '3d_models_value': values_3d if values_3d is not None else 0,
                                                    'scripts_value': values_scripts if values_scripts is not None else 0,
                                                    'unity_value': values_unity if values_unity is not None else 0,
                                                    'others_value': values_others if values_others is not None else 0,
                                                    'user_profile': user_profile})


@require_POST
def delete_file_from_storage(request, category, file_id):
    uploaded_file = get_object_or_404(UploadedFile, pk=file_id)
    file_path = uploaded_file.file.path
    if os.path.exists(file_path):
        os.remove(file_path)

    uploaded_file.value = 0
    uploaded_file.save()

    uploaded_file.delete()

    return redirect('assets_list', category=category)

