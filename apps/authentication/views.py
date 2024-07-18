import json
import pytz
from decouple import config
from core.settings import CORE_DIR
from django.contrib import messages
from cryptography.fernet import Fernet
from datetime import datetime, timedelta
from .models import AuthEmail, PasswordReset
from apps.home.models import Profile, Office
from django.shortcuts import render, redirect
from django.contrib.auth.hashers import check_password
from django.contrib.auth.models import User, Permission
from django.contrib.auth import authenticate, login, logout
from .forms import LoginForm, SignUpForm, PasswordResetForm
from apps.tasks import confirm_register_email, reset_password_email, reset_password_confirmation_email


admin_group = config('ADMIN_USERS', 'admin').split(',')

staff_group = config('STAFF_USERS', 'admin').split(',')

collaborators_key = config('COLLABORATORS_KEY', 'collaborator')

collaborators_permissions_list = [
    'view_client',
    'view_office',
]

admin_permissions_list = [
                             'add_bill',
                             'change_bill',
                             'delete_bill',
                             'view_bill',
                             'add_client',
                             'change_client',
                             'delete_client',
                             'change_collaborator',
                             'delete_collaborator',
                             'add_document',
                             'change_document',
                             'delete_document',
                             'view_document',
                             'add_office',
                             'change_office',
                             'delete_office',
                             'add_branch',
                             'change_branch',
                             'delete_branch',
                             'view_branch',
                         ] + collaborators_permissions_list

staff_permissions_list = [
                             'add_logentry',
                             'change_logentry',
                             'delete_logentry',
                             'view_logentry',
                             'add_group',
                             'change_group',
                             'delete_group',
                             'view_group',
                             'add_permission',
                             'change_permission',
                             'delete_permission',
                             'view_permission',
                             'add_user',
                             'change_user',
                             'delete_user',
                             'view_user',
                             'add_contenttype',
                             'change_contenttype',
                             'delete_contenttype',
                             'view_contenttype',
                             'add_session',
                             'change_session',
                             'delete_session',
                             'view_session',
                         ] + collaborators_permissions_list

admin_permissions = Permission.objects.filter(codename__in=admin_permissions_list)

collaborators_permissions = Permission.objects.filter(codename__in=collaborators_permissions_list)

staff_permissions = Permission.objects.filter(codename__in=staff_permissions_list)


def encrypt_tag(key, message):
    f = Fernet(key)
    token = f.encrypt(str(message).encode())
    return token


def decrypt_tag(key, token):
    f = Fernet(key.encode())
    decrypted = f.decrypt(token.encode())
    return decrypted


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            try:
                auth = AuthEmail.objects.get(user__username=username).is_confirmed
            except AuthEmail.DoesNotExist:
                auth = None

            if user and auth:
                login(request, user)
                profile, created = Profile.objects.get_or_create(user=user)
                if created or profile.first_access:
                    return redirect("fill_profile")
                else:
                    return redirect("home")

            else:
                logout(request)
                try:
                    user = User.objects.get(username=username)
                    valid_password = check_password(password, user.password)
                    if not valid_password:
                        msg = 'Invalid credentials'

                except User.DoesNotExist:
                    valid_password = False
                    msg = 'Invalid credentials'

                if valid_password:
                    if auth is None:
                        f_key = Fernet.generate_key()
                        auth_object = AuthEmail(
                            user=user,
                            token=encrypt_tag(f_key, username).decode(),
                            key=f_key.decode(),
                        )
                        auth_object.save()

                        confirm_register_email.delay(username, auth_object.token)
                        messages.error(request, f"Authentication key created, check your email.")

                    elif not auth:
                        messages.error(request, 'User has not been activated')

                    else:
                        messages.error(request, 'User blocked')

        else:
            msg = 'Error validating the form'

    return render(request, "accounts/login.html", {"form": form, "msg": msg})


def register_user(request):
    msg = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")

            if username.endswith('@infinitefoundry.com'):
                form.save()
            else:
                messages.error(request, 'Only collaborators can register.')
                return redirect('register')

            user = authenticate(username=username, password=raw_password)
            user.is_active = False
            user.save()

            f_key = Fernet.generate_key()
            auth = AuthEmail(
                user=user,
                token=encrypt_tag(f_key, username).decode(),
                key=f_key.decode(),
            )
            auth.save()

            confirm_register_email.delay(username, auth.token)
            messages.success(request, 'User created! Please confirm your email to login.')
            return redirect('home')
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})


def reconfirm_email(request):
    user = User.objects.get(username=request.POST.get('email'))
    key = Fernet.generate_key()
    auth_object = AuthEmail.objects.get(user=user)
    auth_object.token = encrypt_tag(key, user.username).decode()
    auth_object.key = key.decode()
    auth_object.save()

    confirm_register_email.delay(user.username, auth_object.token)
    messages.success(request, 'Email sent! Please confirm your email to login.')
    return redirect('home')


def validate_email(request, token):
    try:
        auth_object = AuthEmail.objects.get(token=token)
    except AuthEmail.DoesNotExist:
        messages.error(request, 'Invalid registration token')
        return redirect('home')

    decrypted_token = decrypt_tag(auth_object.key, token).decode()
    valid_token = decrypted_token == auth_object.user.username
    expired = datetime.now(tz=pytz.utc) - auth_object.created_at > timedelta(hours=24)
    expired = False if valid_token and auth_object.is_confirmed else expired

    if not valid_token:
        messages.error(request, 'Invalid token')

    elif valid_token and not auth_object.is_confirmed and not expired:
        auth_object.is_confirmed = True
        auth_object.confirmed_at = datetime.now()
        auth_object.save()
        auth_object.user.is_active = True

        if auth_object.user.username in admin_group:
            auth_object.user.user_permissions.set(admin_permissions)
        elif auth_object.user.username in staff_group:
            auth_object.user.user_permissions.set(staff_permissions)
        elif collaborators_key in auth_object.user.username:
            auth_object.user.user_permissions.set(collaborators_permissions)
        else:
            pass

        auth_object.user.save()

        messages.success(request, 'Email confirmed! You can now login.')

    elif not auth_object.is_confirmed and expired:
        auth_object.delete()
        messages.error(request, 'Token expired!')

    elif auth_object.is_confirmed:
        messages.info(request, 'Email already confirmed')

    else:
        messages.error(request, 'Invalid token')

    return redirect('home')


def request_reset_password(request):
    if request.method == 'POST':
        username = request.POST.get('email')
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('home')

        key = Fernet.generate_key()
        pass_reset_object, created = PasswordReset.objects.get_or_create(user=user)
        pass_reset_object.token = encrypt_tag(key, user.username).decode()
        pass_reset_object.key = key.decode()
        pass_reset_object.created_at = datetime.now(tz=pytz.utc)
        pass_reset_object.save()

        reset_password_email.delay(username, pass_reset_object.token)
        messages.success(request, 'Email sent! Check your email to password reset.')
        return redirect('home')

    else:
        return redirect('home', {'msg': 'Request error'})


def reset_password_page(request):
    if request.method == 'POST':
        user = User.objects.get(username=request.session['reset_password']['username'])
        form = PasswordResetForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            PasswordReset.objects.get(user=user).delete()
            del request.session['reset_password']

            reset_password_confirmation_email.delay(user.username)
            messages.success(request, 'Password changed! You can now login.')
            return redirect('login')

        else:
            messages.error(request, 'Form is not valid')
            context = {
                'form': form,
            }

    else:
        token = request.session['reset_password'].get('token')
        username = request.session['reset_password'].get('username')

        if not token:
            messages.error(request, 'Invalid session. Try to open the link again.')
            return redirect('home')

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            messages.error(request, 'User not found')
            return redirect('home')

        form = PasswordResetForm(user=user)
        del request.session['reset_password']['token']
        request.session.modified = True

        try:
            PasswordReset.objects.get(user=user)
        except PasswordReset.DoesNotExist:
            messages.error(request, 'Invalid token')
            return redirect('home')

        context = {
            'form': form,
        }

    return render(request, 'accounts/reset_password.html', context)


def reset_password_validation(request, token):
    try:
        pass_reset_object = PasswordReset.objects.get(token=token)
        decrypted_token = decrypt_tag(pass_reset_object.key, token).decode()
        valid_token = decrypted_token == pass_reset_object.user.username
        expired = datetime.now(tz=pytz.utc) - pass_reset_object.created_at > timedelta(hours=24)

        if not valid_token:
            messages.error(request, 'Invalid token')
        elif expired:
            messages.error(request, 'Token expired, request a new one')
        else:
            request.session['reset_password'] = {
                'username': pass_reset_object.user.username,
                'token': token,
            }
            return redirect('reset_password_page')

        pass_reset_object.delete()

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid password reset token')

    return redirect('home')


def fill_profile(request):
    if request.method == "POST":
        user_object = request.user
        profile, created = Profile.objects.get_or_create(user=user_object)

        user_object.first_name = request.POST['first_name'].title()
        user_object.last_name = request.POST['last_name'].title()
        user_object.email = user_object.username

        profile.office = Office.objects.get(id=request.POST['office']) if request.POST.get(
            'office') else profile.office
        profile.street = request.POST.get('street', profile.street)
        profile.street_number = request.POST.get('street_number', profile.street_number)
        profile.city = request.POST.get('city', profile.city)
        profile.state = request.POST.get('state', profile.state)
        profile.country = request.POST.get('country', profile.country)
        profile.about = request.POST.get('about', profile.about)
        profile.first_access = False
        profile.avatar = request.FILES.get('avatar', profile.avatar)
        profile.phone = request.POST.get('phone', profile.phone)
        profile.birthday = request.POST.get('birthday', profile.birthday)
        profile.position = request.POST.get('position', profile.position)

        user_object.save()
        profile.save()

        if not profile.qrcode:
            profile.generate_qrcode()

        return redirect("profile")

    else:
        try:
            user_profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            user_profile = None

        context = {
            "world": json.load(open(f'{CORE_DIR}/apps/static/assets/world.json', 'r', encoding='utf-8')),
            "offices": Office.objects.all(),
            "user": user_profile,
        }

        return render(request, "home/profile/wizard.html", context)
