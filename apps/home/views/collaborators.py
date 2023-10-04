from django.shortcuts import render
from apps.home.models import Profile
from django.core.paginator import Paginator
from django.db.models import Q


def get_paginated_collaborators(request, **kwargs):
    collaborators = Profile.objects.all()

    # Loop through all the filters provided in kwargs
    for key, value in kwargs.items():
        # Check if the filter key is a valid field in your Profile model
        if key in Profile._meta.get_fields():
            # If the filter value is not empty, filter the queryset
            if value:
                # If you want to apply 'OR' logic between filters, use Q objects
                collaborators = collaborators.filter(Q(**{key: value}))

    exclude_query = Q(user__is_superuser=True) | Q(user=request.user)

    collaborators = collaborators.exclude(exclude_query)
    collaborators = collaborators.order_by('user__first_name')

    paginator = Paginator(collaborators, 6)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return page_obj


def page_list(request):
    context = {
        'collaborators': get_paginated_collaborators(request, **request.GET),
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/collaborators-list.html', context)


def details(request, name):
    full_name_from_post = name.replace('-', ' ').title()

    for user in Profile.objects.all():
        print(user.user.get_full_name(), full_name_from_post)
        if user.user.get_full_name() == full_name_from_post:
            user_id = user.user.id
            break
        else:
            user_id = 1

    context = {
        'collaborator': Profile.objects.get(user__id=user_id),
        'user_profile': Profile.objects.get(user=request.user),
    }

    return render(request, 'home/collaborator-page.html', context)
