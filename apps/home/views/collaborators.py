from django.shortcuts import render, redirect, get_object_or_404
from apps.home.models import Profile, Office, Document
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponse, Http404
from django.db.models import Q
import datetime
import os


def get_paginated_collaborators(request, **kwargs):
    collaborators = Profile.objects.filter(user__is_superuser=False).order_by('user__first_name')

    paginator = Paginator(collaborators, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


def page_list(request):
    context = {
        'collaborators': get_paginated_collaborators(request, **request.GET),
        'user_profile': Profile.objects.get(user=request.user),
        'offices': Office.objects.all(),
    }

    return render(request, 'home/collaborators-list.html', context)


def details(request, slug):

    collab = Profile.objects.get(slug=slug)

    if request.method == 'POST':
        collab.about = request.POST.get('about', collab.about)
        collab.address = request.POST.get('address', collab.address)
        collab.city = request.POST.get('city', collab.city)
        collab.country = request.POST.get('country', collab.country)
        collab.user.first_name = request.POST.get('first_name', collab.user.first_name)
        collab.user.last_name = request.POST.get('last_name', collab.user.last_name)
        collab.postal_code = request.POST.get('postal_code', collab.postal_code)
        collab.state = request.POST.get('state', collab.state)
        collab.save()
        collab.user.save()

        return redirect(
            'collaborator_details',
            slug=collab.slug,
        )

    edit_mode = request.GET.get('edit')

    if edit_mode is not None:
        edit_mode = True
    else:
        edit_mode = False

    context = {
        'collaborator': collab,
        'user_profile': Profile.objects.get(user=request.user),
        'edit_mode': edit_mode,
        'date': datetime.datetime.now().date(),
    }

    return render(request, 'home/collaborator-page.html', context)


def new(request):
    new_collab = Collaborator(
        birthday=request.POST['birthday'],
        admission=request.POST['admission'],
        email=request.POST['email'],
        contract=request.POST['contract'],
        first_name=request.POST['first_name'],
        last_name=request.POST['last_name'],
        office=Office.objects.get(id=request.POST['office'])
    )

    new_collab.save()

    return redirect('collaborators_list')


def newdoc(request, collab_id):
    new_document = Document(
        user=User.objects.get(id=collab_id),
        category=request.POST.get('category', 'None'),
        description=request.POST['description'],
        expiration=request.POST['expiration'],
        file=request.FILES['file'],
        name=request.POST['name'],
    )

    new_document.save()

    return redirect('collaborator_details', slug=Profile.objects.get(id=collab_id).slug)


def change_status(request, collab_id):
    collab = Profile.objects.get(id=collab_id)
    collab.active = not collab.active

    collab.save()

    return redirect('collaborators_list')


def delete_document(request, slug, document_id):
    document = get_object_or_404(Document, id=document_id)
    document_path = document.file.path
    if os.path.exists(document_path):
        os.remove(document_path)

    document.delete()

    return redirect('collaborator_details', slug=slug)


def download_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_path = document.file.path

    if os.path.exists(document_path):
        with open(document_path, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type='application/force-download')
            response['Content-Disposition'] = 'inline; filename=' + os.path.basename(document_path)
            return response

    raise Http404
