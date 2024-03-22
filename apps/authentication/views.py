import json
import pytz
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm, PasswordResetForm
from apps.home.models import Profile, Office
from django.contrib.auth.models import User, Permission
from core.settings import CORE_DIR, EMAIL_HOST_USER
from django.core.mail import send_mail
from cryptography.fernet import Fernet
from apps.authentication.models import AuthEmail, PasswordReset
from datetime import datetime, timedelta
from decouple import config
from django.contrib import messages
from django.contrib.auth.hashers import check_password


def encrypt_tag(key, message):
    f = Fernet(key)
    token = f.encrypt(str(message).encode())
    return token


def decrypt_tag(key, token):
    f = Fernet(key.encode())
    decrypted = f.decrypt(token.encode())
    return decrypted


def confirm_register_email(email, auth_token):
    subject = 'Register confirmation'

    message = (f'Hello! Please click the link below to confirm your email.\n\n'
               f'{config("WEBSITE_URL")}/validate/{auth_token}\n\n'
               f'If you did not request this, please ignore this email.\n\n'
               f'Thanks, Infinite Foundry.')

    email_from = EMAIL_HOST_USER
    to_email = [email]
    send_mail(subject, message, email_from, to_email)


def reset_password_email(username, token):
    subject = 'Password reset'

    message = (f'Hello! Please click the link below to reset your password.\n\n'
               f'{config("WEBSITE_URL")}/reset-password/{token}\n\n'
               f'If you did not request this, please ignore this email.\n\n'
               f'Thanks, Infinite Foundry.')

    email_from = EMAIL_HOST_USER
    to_email = [username]
    send_mail(subject, message, email_from, to_email)


def reset_password_confirmation_email(username):
    subject = 'Password changed'

    date = datetime.now(tz=pytz.utc).strftime("%d/%m/%Y %H:%M:%S")

    message = (f'Hello! Your password has been changed at {date} UTC.\n\n'
               f'If you did not request this, please contact us.\n\n'
               f'Thanks, Infinite Foundry.')

    email_from = EMAIL_HOST_USER
    to_email = [username]
    send_mail(subject, message, email_from, to_email)


def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                check_profile = Profile.objects.filter(user=user)
                check_profile = check_profile[0] if check_profile else None
                if check_profile:
                    if not check_profile.first_access:
                        return redirect("home")
                    else:
                        request.session['registration_data'] = {
                            'username': check_profile.user.username,
                            'logged': 'true',
                        }
                else:
                    request.session['registration_data'] = {
                        'username': user.username,
                        'logged': 'true',
                    }

                return redirect("fill_profile")

            else:
                try:
                    user = User.objects.get(username=username)
                    auth = AuthEmail.objects.get(user=user)

                    if not user.is_active and not auth.is_confirmed and check_password(password, user.password):
                        messages.error(request, 'User has not been activated, confirm your email.')
                    else:
                        msg = 'Invalid credentials'
                except User.DoesNotExist:
                    msg = 'Invalid credentials'
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

            request.session['registration_data'] = {
                'username': username,
            }

            collaborators_permissions_list = [
                'view_client',
                'view_office',
            ]

            collaborators_permissions = Permission.objects.filter(codename__in=collaborators_permissions_list)

            if '@infinitefoundry.com' in user.username:
                user.user_permissions.set(collaborators_permissions)

            user.is_active = False
            user.save()

            key = Fernet.generate_key()
            auth_object = AuthEmail(
                user=user,
                auth_token=encrypt_tag(key, username).decode(),
                auth_key=key.decode(),
            )
            auth_object.save()

            confirm_register_email(username, auth_object.auth_token)
            messages.success(request, 'User created! Please confirm your email to login.')
            return redirect('home')
        else:
            msg = 'Form is not valid'
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg": msg, "success": success})


def fill_profile(request):
    if request.method == "POST":
        success = True

        user_object = User.objects.get(username=request.session['registration_data']['username'])

        user_object.first_name = request.POST['first_name'].title()
        user_object.last_name = request.POST['last_name'].title()
        user_object.email = request.session['registration_data']['username']

        # Check if user already exists
        if Profile.objects.filter(user__username=request.session['registration_data']['username']).exists():
            profile = Profile.objects.get(user__username=request.session['registration_data']['username'])
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

        else:
            profile = Profile(
                user=user_object,
                office=Office.objects.get(id=request.POST['office']) if request.POST.get('office') else None,
                street=request.POST['street'],
                street_number=request.POST['street_number'],
                city=request.POST['city'],
                state=request.POST['state'],
                country=request.POST['country'],
                about=request.POST['about'],
                first_access=False,
                phone=request.POST['phone'],
                birthday=request.POST['birthday'],
                position=request.POST['position'],
            )

            profile.avatar = request.FILES.get('avatar', profile.avatar)

        user_object.save()
        profile.save()

        msg = 'User created! You can now <a href="/login/">login</a>'

        if 'logged' in request.session['registration_data']:
            del request.session['registration_data']
            return redirect("profile")
        else:
            del request.session['registration_data']
            return redirect("/login/", {"msg": msg, "success": success})

    else:
        user_profile = Profile.objects.filter(user__username=request.session['registration_data']['username']) if \
            request.session.get('registration_data') else None
        user_profile = user_profile[0] if user_profile else None

        context = {
            "world": json.load(open(f'{CORE_DIR}/apps/static/assets/world.json', 'r', encoding='utf-8')),
            "offices": Office.objects.all(),
            "user": user_profile,
        }

        return render(request, "home/profile-wizard.html", context)


def validate_email(request, auth_token):
    try:
        auth_object = AuthEmail.objects.get(auth_token=auth_token)
    except AuthEmail.DoesNotExist:
        messages.error(request, 'Invalid token')
        return redirect('home')

    if auth_object:
        decrypted_token = decrypt_tag(auth_object.auth_key, auth_token).decode()
        expired = datetime.now(tz=pytz.utc) - auth_object.created_at > timedelta(hours=24)
        if (decrypted_token == auth_object.user.username
                and not auth_object.is_confirmed
                and not expired):
            auth_object.is_confirmed = True
            auth_object.confirmed_at = datetime.now()
            auth_object.save()
            user = User.objects.get(username=auth_object.user.username)
            user.is_active = True
            user.save()
            messages.success(request, 'Email confirmed! You can now login.')
            return redirect('login')
        elif not auth_object.is_confirmed and expired:
            user = User.objects.get(username=auth_object.user.username)
            auth_object.delete()
            messages.error(request, 'Token expired! Try to register again.')
            return redirect('home')
        elif auth_object.is_confirmed:
            messages.info(request, 'Email already confirmed')
            return redirect('home')
        else:
            messages.error(request, 'Invalid token')
            return redirect('home')


def reconfirm_email(request):
    user = User.objects.get(username=request.POST.get('email'))
    key = Fernet.generate_key()
    auth_object = AuthEmail.objects.get(user=user)
    auth_object.auth_token = encrypt_tag(key, user.username).decode()
    auth_object.auth_key = key.decode()
    auth_object.save()

    confirm_register_email(user.username, auth_object.auth_token)
    messages.success(request, 'Email sent! Please confirm your email to login.')
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
        pass_reset_object.used = False
        pass_reset_object.created_at = datetime.now(tz=pytz.utc)
        pass_reset_object.save()

        reset_password_email(username, pass_reset_object.token)
        messages.success(request, 'Email sent! Check your email to password reset.')
        return redirect('home')

    else:
        return redirect('home', {'msg': 'Request error'})


def reset_password_validation(request, token):
    try:
        pass_reset_object = PasswordReset.objects.get(token=token)
        decrypted_token = decrypt_tag(pass_reset_object.key, token).decode()
        expired = datetime.now(tz=pytz.utc) - pass_reset_object.created_at > timedelta(hours=24)
        if decrypted_token != pass_reset_object.user.username:
            messages.error(request, 'Invalid token')
        elif expired:
            messages.error(request, 'Token expired, try again')
        else:
            request.session['reset_password'] = {
                'username': pass_reset_object.user.username,
                'token': token,
            }
            return redirect('reset_password_page')

        pass_reset_object.delete()

    except PasswordReset.DoesNotExist:
        messages.error(request, 'Invalid token')

    return redirect('home')


def reset_password_page(request):
    if request.method == 'POST':
        user = User.objects.get(username=request.session['reset_password']['username'])
        form = PasswordResetForm(user=user, data=request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Password changed! You can now login.')
            del request.session['reset_password']
            PasswordReset.objects.get(user=user).delete()
            reset_password_confirmation_email(user.username)
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
