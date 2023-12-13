from django.shortcuts import render, redirect, get_object_or_404
from apps.home.models import Profile, Unit, Collaborator, UploadedDocument
from django.core.paginator import Paginator
from django.db.models import Q
import os


def get_paginated_collaborators(request, **kwargs):
    collaborators = Collaborator.objects.all()

    # # Loop through all the filters provided in kwargs
    # for key, value in kwargs.items():
    #     # Check if the filter key is a valid field in your Profile model
    #     if key in Profile._meta.get_fields():
    #         # If the filter value is not empty, filter the queryset
    #         if value:
    #             # If you want to apply 'OR' logic between filters, use Q objects
    #             collaborators = collaborators.filter(Q(**{key: value}))
    #
    # exclude_query = Q(user__is_superuser=True) | Q(user=request.user)
    #
    # collaborators = collaborators.exclude(exclude_query)
    # collaborators = collaborators.order_by('user__first_name')

    paginator = Paginator(collaborators, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


def page_list(request):
    context = {
        'collaborators': get_paginated_collaborators(request, **request.GET),
        'user_profile': Profile.objects.get(user=request.user),
        'offices': Unit.objects.all(),
    }

    return render(request, 'home/collaborators-list.html', context)


def details(request, collab_first_name, collab_last_name, collab_id):

    collab = Collaborator.objects.get(id=collab_id)

    if request.method == 'POST':
        collab.about = request.POST.get('about', collab.about)
        collab.address = request.POST.get('address', collab.address)
        collab.city = request.POST.get('city', collab.city)
        collab.country = request.POST.get('country', collab.country)
        collab.first_name = request.POST.get('first_name', collab.first_name)
        collab.last_name = request.POST.get('last_name', collab.last_name)
        collab.postal_code = request.POST.get('postal_code', collab.postal_code)
        collab.state = request.POST.get('state', collab.state)
        collab.save()

        return redirect(
            'collaborator_details',
            collab_first_name=collab.first_name,
            collab_id=collab.id,
            collab_last_name=collab.last_name,
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
        'document_list': UploadedDocument.objects.filter(collab=collab),
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
        office=Unit.objects.get(id=request.POST['office'])
    )

    new_collab.save()

    return redirect('collaborators_list')


def newdoc(request, collab_id):
    collab = Collaborator.objects.get(id=collab_id)

    new_document = UploadedDocument(
        category=request.POST['category'],
        collab=collab,
        description=request.POST['description'],
        expiration=request.POST['expiration'],
        file=request.FILES['file'],
        name=request.POST['name'],
        uploaded=request.POST['uploaded'],
    )

    new_document.save()

    return redirect('collaborator_details', collab_first_name=collab.first_name, collab_last_name=collab.last_name,
                    collab_id=collab.id)


def change_status(request, collab_id):
    collab = Collaborator.objects.get(id=collab_id)
    collab.status = not collab.status

    collab.save()

    return redirect('collaborators_list')


def delete_document(request, document_id):
    uploaded_document = get_object_or_404(UploadedDocument, id=document_id)
    document_path = uploaded_document.file.path
    if os.path.exists(document_path):
        os.remove(document_path)

    collab_id = uploaded_document.collab.id
    collab_first_name = uploaded_document.collab.first_name
    collab_last_name = uploaded_document.collab.last_name

    uploaded_document.delete()

    return redirect('collaborator_details',
                    collab_first_name=collab_first_name,
                    collab_last_name=collab_last_name,
                    collab_id=collab_id)


