import json
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from .forms import LoginForm, SignUpForm
from apps.home.models import Profile, Office
from django.contrib.auth.models import User
from core.settings import BASE_DIR, CORE_DIR


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

                return redirect("fill_profile")

            else:
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
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")

            user = authenticate(username=username, password=raw_password)

            request.session['registration_data'] = {
                'username': username,
            }

            return redirect('fill_profile')
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
            profile.office = Office.objects.get(id=request.POST['office'])
            profile.street = request.POST.get('street', profile.street)
            profile.street_number = request.POST.get('street_number', profile.street_number)
            profile.city = request.POST.get('city', profile.city)
            profile.state = request.POST.get('state', profile.state)
            profile.country = request.POST.get('country', profile.country)
            profile.about = request.POST.get('about', profile.about)
            profile.first_access = False
            profile.avatar = request.FILES.get('avatar', profile.avatar)

        else:
            profile = Profile(
                user=user_object,
                office=Office.objects.get(id=request.POST['office']),
                street=request.POST['street'],
                street_number=request.POST['street_number'],
                city=request.POST['city'],
                state=request.POST['state'],
                country=request.POST['country'],
                about=request.POST['about'],
                first_access=False,
            )

            profile.avatar = request.FILES.get('avatar', profile.avatar)

        profile.save()
        user_object.save()

        # profile.postal_code = request.POST.get('postal_code', None)
        # profile.phone = request.POST['phone']

        msg = 'User created! You can now <a href="/login/">login</a>'

        if 'logged' in request.session['registration_data']:
            del request.session['registration_data']['logged']
            return redirect("profile")
        else:
            return redirect("/login/", {"msg": msg, "success": success})

    else:
        context = {
            "world": json.load(open(f'{CORE_DIR}/apps/static/assets/world.json', 'r', encoding='utf-8')),
            "offices": Office.objects.all(),
            "user": Profile.objects.filter(user__username=request.session['registration_data'][
                'username'])[0] if Profile.objects.filter(user__username=request.session['registration_data'][
                'username']) else "",
        }

        return render(request, "home/profile-wizard.html", context)
