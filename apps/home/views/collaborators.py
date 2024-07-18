from django.shortcuts import render, redirect, get_object_or_404
from apps.home.models import Profile, Office, Document, BankAccount, BANKS
from django.core.files.storage import default_storage
from django.http import HttpResponse, Http404
from django.contrib.auth.models import User
from django.db.models import Q
import datetime
import os


def check_expired_documents():
    expired_documents = Document.objects.filter(Q(expiration__lt=datetime.datetime.now().date()) & Q(expired=False))
    for doc in expired_documents:
        doc.expired = True
        doc.save()


def filter_documents_objects(user, filters):
    documents = Document.objects.filter(user=user)

    if filters:
        filters_list = filters.split('&')

        category = 'all'
        from_date, to_date = False, False
        expired, up_to_date = True, True

        for item in filters_list:
            from_date = datetime.datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith(
                'from') else from_date
            to_date = datetime.datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            category = item.split('=')[1] if item.startswith('category') else category

            if from_date and to_date and from_date < to_date:
                documents = documents.filter(expiration__gte=from_date)
                documents = documents.filter(expiration__lte=to_date)
            elif from_date:
                documents = documents.filter(expiration__gte=from_date)
            elif to_date:
                documents = documents.filter(expiration__lte=to_date)

            if category != 'all':
                documents = documents.filter(category=category if category else None)

    return documents


def sort_documents_objects(documents, sorted_by, sort_type):
    if sorted_by is not None:
        sorted_by = sorted_by.replace('-', '_')
    else:
        sorted_by = ''

    documents = sorted(documents, key=lambda document: getattr(document, sorted_by, ''))

    if sort_type == 'desc':
        documents = reversed(documents)

    return documents


def get_permission(request, permission_type, model='bill'):
    return request.user.has_perm(f'home.{permission_type}_{model}')


def page_list(request, filters=None, sorted_by=None, sort_type=None):
    check_expired_documents()

    collaborators = filter_collaborators_objects(request, filters)
    collaborators = sort_collaborators_objects(collaborators, sorted_by, sort_type)

    collaborators = list(collaborators)

    min_aso_date = sorted(collaborators, key=lambda collaborator: collaborator.aso if collaborator.aso else datetime.date.max)[0].aso if len(collaborators) > 0 else 0
    max_aso_date = sorted(collaborators, key=lambda collaborator: collaborator.aso if collaborator.aso else datetime.date.min)[-1].aso if len(collaborators) > 0 else 0

    context = {
        'sorted_by': sorted_by.replace('-', '_') if sorted_by else None,
        'sort_type': sort_type.replace('-', '_') if sort_type else None,
        'filters': filters,
        'collaborators': collaborators,
        'user_profile': Profile.objects.get(user=request.user),
        'offices': Office.objects.all(),
        'min_aso_date': min_aso_date,
        'max_aso_date': max_aso_date,
    }

    return render(request, 'home/collaborators/home.html', context)


def details(request, slug, sorted_by=None, sort_type=None, filters=None):
    if not get_permission(request, 'view', 'document'):
        context = {
            'user_profile': Profile.objects.get(user=request.user),
        }
        return render(request, 'home/page-404.html', context)

    check_expired_documents()

    collab = Profile.objects.get(slug=slug)
    documents = filter_documents_objects(collab.user, filters)
    documents = sort_documents_objects(documents, sorted_by, sort_type)

    aso_document = Document.objects.filter(user=collab.user, category='ASO', expiration__isnull=False).order_by(
        'expiration').last()

    days_to_aso = (aso_document.expiration - datetime.datetime.now().date()).days if aso_document else None

    expired_documents_count = Document.objects.filter(user=collab.user, expired=True).count()

    context = {
        'sorted_by': sorted_by.replace('-', '_') if sorted_by else None,
        'sort_type': sort_type.replace('-', '_') if sort_type else None,
        'filters': filters,
        'collaborator': collab,
        'collaborator_documents': documents,
        'collaborator_all_documents': Document.objects.filter(user=collab.user).count(),
        'user_profile': Profile.objects.get(user=request.user),
        'aso_date': aso_document.expiration if aso_document else None,
        'aso_expiration': days_to_aso,
        'expired_documents': expired_documents_count,
        'expired_documents_percentage': (expired_documents_count / Document.objects.filter(
            user=collab.user).count()) * 100 if Document.objects.filter(user=collab.user).count() > 0 else 0,
        'banks': BANKS.items(),
    }

    return render(request, 'home/collaborators/details.html', context)


def newdoc(request, collab_id):
    new_document = Document(
        user=User.objects.get(id=collab_id),
        category=request.POST['category'],
        description=request.POST['description'],
        expiration=request.POST['expiration'] if request.POST['expiration'] != '' else None,
        file=request.FILES['file'],
        name=request.POST['name'],
        uploaded_by=request.user,
        shared=True if request.POST.get('shared', False) else False,
    )

    new_document.save()

    return redirect('collaborator_details', slug=Profile.objects.get(user__id=collab_id).slug)


def change_status(request, collab_id):
    collab = Profile.objects.get(id=collab_id)
    collab.user.is_active = not collab.user.is_active

    collab.user.save()

    return redirect('collaborators_list')


def delete_document(request, slug, document_id):
    document = get_object_or_404(Document, id=document_id)
    document_path = document.file
    if document_path:
        document_path.delete(save=False)

    document.delete()

    return redirect('collaborator_details', slug=slug)


def edit_document(request, slug, document_id):
    document = Document.objects.get(id=document_id)
    if request.method == 'POST':
        expiration = request.POST.get('expiration', document.expiration)

        document.category = request.POST.get('category', document.category)
        document.description = request.POST.get('description', document.description)
        document.expiration = expiration if expiration != '' else None
        document.name = request.POST.get('name', document.name)
        document.shared = True if request.POST.get('shared', False) else False
        document.save()

    return redirect('collaborator_details', slug=slug)


def download_document(request, document_id):
    document = get_object_or_404(Document, id=document_id)

    document_name = document.file.name
    file_content = default_storage.open(document_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{document_name.split("/")[-1]}"'
    return response


def download_collaborator_qrcode(request, slug):
    collaborator = get_object_or_404(Profile, slug=slug)
    qr = collaborator.qrcode

    file_name = qr.name
    file_content = default_storage.open(file_name).read()
    response = HttpResponse(file_content, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{file_name.split("/")[-1]}"'
    return response


def sort_docs(request, slug):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_documents', sorted_by=sorted_by, sort_type=sort_type, filters=filters,
                        slug=slug)
    elif sorted_by != '':
        return redirect('sorted_documents', sorted_by=sorted_by, sort_type=sort_type, slug=slug)
    elif filters != 'None':
        return redirect('filtered_documents', filters=filters, slug=slug)
    else:
        return redirect('collaborator_details', slug=slug)


def filter_docs(request, slug):
    from_date = request.POST['from']
    to_date = request.POST['to']
    category = request.POST['category']
    expired = request.POST.get('expired')

    filter_list = [
        f'from={from_date}' if from_date != '' and from_date != to_date else '%',
        f'to={to_date}' if to_date != '' and from_date != to_date else '%',
        f'category={category}' if category != 'all' else '%',
    ]

    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    if request.POST['sort_by'] != 'None' and filter_string != '%':
        return redirect('sorted_filtered_documents',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string, slug=slug)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_documents',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'], slug=slug)
    elif filter_string == '%':
        return redirect('collaborator_details', slug=slug)
    else:
        return redirect('filtered_documents', filters=filter_string, slug=slug)


def filter_collaborators(request):
    office = request.POST['office']
    group = request.POST['group']
    disabled = request.POST.get('disabled_filter', None)
    active = request.POST.get('active_filter', None)

    filter_list = [
        f'office={office}' if office != 'all' else '%',
        f'group={group}' if group != 'all' else '%',
        f'disabled=off' if not disabled else '%',
        f'active=off' if not active else '%',
    ]

    filter_string = '&'.join(filter_list)
    if filter_string.startswith('%&'):
        filter_string = filter_string[2:]
    if filter_string.endswith('&'):
        filter_string = filter_string[:-1]

    filter_string = filter_string.replace('%&', '')
    filter_string = filter_string.replace('/', '-')
    filter_string = filter_string[:-2] if filter_string.endswith('&%') else filter_string

    if request.POST['sort_by'] != 'None' and filter_string != '%':
        return redirect('sorted_filtered_collaborators',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'],
                        filters=filter_string)
    elif filter_string == '%' and request.POST['sort_by'] != 'None':
        return redirect('sorted_collaborators',
                        sorted_by=request.POST['sort_by'].replace('_', '-'),
                        sort_type=request.POST['sort_type'])
    elif filter_string == '%':
        return redirect('collaborators_list')
    else:
        return redirect('filtered_collaborators', filters=filter_string)


def sort_collaborators(request):
    sorted_by = request.POST['sort_by'].replace('_', '-') if request.POST.get('sort_by', False) else ''
    sort_type = 'asc' if request.POST.get('asc', False) else 'desc'
    filters = request.POST.get('filters', 'None')

    if sorted_by == 'identification':
        sorted_by = 'id'

    if sorted_by != '' and filters != 'None':
        return redirect('sorted_filtered_collaborators', sorted_by=sorted_by, sort_type=sort_type, filters=filters)
    elif sorted_by != '':
        return redirect('sorted_collaborators', sorted_by=sorted_by, sort_type=sort_type)
    elif filters != 'None':
        return redirect('filtered_collaborators', filters=filters)
    else:
        return redirect('collaborators_list')


def filter_collaborators_objects(request, filters):
    if request.user.is_staff:
        collaborators = Profile.objects.filter(user__username__endswith='@infinitefoundry.com').order_by('user__first_name')
    else:
        # Remove admin users from collaborators list
        collaborators = Profile.objects.filter(user__username__endswith='@infinitefoundry.com').exclude(user__username__in=[
            'admin@infinitefoundry.com'])

    groups = {
        'admin': [
            'admin@infinitefoundry.com',
            'vitorhugo@infinitefoundry.com',
        ],
        'financial': [
            'joaoeisinger@infinitefoundry.com',
            'dieynieleandrade@infinitefoundry.com',
        ]
    }

    if filters:
        filters_list = filters.split('&')

        office, group = 'all', 'all'
        from_date, to_date = None, None
        disabled, active = True, True

        for item in filters_list:
            office = item.split('=')[1] if item.startswith('office') else office
            group = item.split('=')[1] if item.startswith('group') else group
            from_date = datetime.datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith(
                'from') else from_date
            to_date = datetime.datetime.strptime(item.split('=')[1], '%Y-%m-%d') if item.startswith('to') else to_date
            disabled = False if item.startswith('disabled') else disabled
            active = False if item.startswith('active') else active

        if office != 'all':
            collaborators = collaborators.filter(office=office if office else None)

        if group != 'all':
            collaborators = collaborators.filter(user__username__in=groups[group])

        if to_date is not None:
            collaborators = collaborators.filter(birthday__lte=to_date)

        if from_date is not None:
            collaborators = collaborators.filter(birthday__gte=from_date)

        if not disabled:
            collaborators = collaborators.filter(user__is_active=True)

        if not active:
            collaborators = collaborators.filter(user__is_active=False)

    return collaborators


def sort_collaborators_objects(collaborators, sorted_by, sort_type):
    if sorted_by is not None:
        sorted_by = sorted_by.replace('-', '_')
    else:
        sorted_by = ''

    if sorted_by == 'birthday':
        if sort_type == 'asc':
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.birthday if collaborator.birthday else datetime.date.max)
        else:
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.birthday if collaborator.birthday else datetime.date.min)
    elif sorted_by == 'aso':
        if sort_type == 'asc':
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.aso if collaborator.aso else datetime.date.max)
        else:
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.aso if collaborator.aso else datetime.date.min)
    elif sorted_by == 'admission':
        if sort_type == 'asc':
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.admission if collaborator.admission else datetime.date.max)
        else:
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.admission if collaborator.admission else datetime.date.min)
    elif sorted_by == 'id':
        if sort_type == 'asc':
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.identification if collaborator.identification is not None else float('inf'))
        else:
            collaborators = sorted(collaborators, key=lambda
                collaborator: collaborator.identification if collaborator.identification is not None else -1)
    else:
        collaborators = sorted(collaborators, key=lambda collaborator: getattr(collaborator, sorted_by, ''))

    if sort_type == 'desc':
        collaborators = reversed(collaborators)

    return collaborators


def fill_collaborator_initial_infos(request, slug):
    collaborator = Profile.objects.get(slug=slug)

    identification = request.POST.get('identification', collaborator.identification)
    admission = request.POST.get('admission', collaborator.admission)
    cpf = request.POST.get('cpf', collaborator.cpf)

    collaborator.identification = identification if identification else collaborator.identification
    collaborator.admission = admission if admission and admission != '' else collaborator.admission
    collaborator.cpf = cpf if cpf else collaborator.cpf

    collaborator.save()

    return redirect('collaborator_details', slug=slug)


#####################################################


def add_bank_account(request, slug):
    collaborator = Profile.objects.get(slug=slug)

    if not request.user.has_perm('home.add_bankaccount'):
        context = {'user_profile': Profile.objects.get(user=request.user)}
        return render(request, 'home/page-404.html', context)

    bank_account = BankAccount(
        user=collaborator.user,
        bank_code=request.POST['bank'],
        agency=request.POST['agency'],
        account=request.POST['account'],
        account_type=request.POST['account_type'],
        pix=request.POST.get('pix', None),
    )

    bank_account.save()

    return redirect('collaborator_details', slug=slug)


def edit_bank_account(request, slug, bank_account_id):
    if not request.user.has_perm('home.change_bankaccount'):
        context = {'user_profile': Profile.objects.get(user=request.user)}
        return render(request, 'home/page-404.html', context)

    bank_account = get_object_or_404(BankAccount, id=bank_account_id)

    bank_account.bank_code = request.POST.get('bank', bank_account.bank_code)
    bank_account.agency = request.POST.get('agency', bank_account.agency)
    bank_account.account = request.POST.get('account', bank_account.account)
    bank_account.account_type = request.POST.get('account_type', bank_account.account_type)
    bank_account.pix = request.POST.get('pix', bank_account.pix)

    bank_account.save()

    return redirect('collaborator_details', slug=slug)


def delete_bank_account(request, slug, bank_account_id):
    if not request.user.has_perm('home.delete_bankaccount'):
        context = {'user_profile': Profile.objects.get(user=request.user)}
        return render(request, 'home/page-404.html', context)

    bank_account = get_object_or_404(BankAccount, id=bank_account_id)
    bank_account.delete()

    return redirect('collaborator_details', slug=slug)
