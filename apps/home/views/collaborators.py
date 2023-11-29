from django.shortcuts import render, redirect
from apps.home.models import Profile, Office, Collaborator
from django.core.paginator import Paginator
from django.db.models import Q


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
        'offices': Office.objects.all(),
    }

    return render(request, 'home/collaborators-list.html', context)


def details(request, collab_name, collab_id):
    context = {
        'collaborator': Collaborator.objects.get(id=collab_id),
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/collaborator-page.html', context)


def new(request):
    new_collab = Collaborator(
        birthday=request.POST['birthday'],
        admission=request.POST['admission'],
        email=request.POST['email'],
        contract=request.POST['contract'],
        name=request.POST['name'],
        office=Office.objects.get(id=request.POST['office'])
    )

    new_collab.save()

    return redirect('collaborators_list')


def change_status(request, collab_id):
    collab = Collaborator.objects.get(id=collab_id)
    collab.status = not collab.status

    collab.save()

    return redirect('collaborators_list')

