from django.urls import resolve, Resolver404, reverse
from django.shortcuts import redirect
from django.conf import settings
from apps.home.models import Profile


class SessionExpiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Se a view já retornou um redirect, respeite
        if response.status_code in (301, 302, 303, 307, 308):
            return response

        try:
            match = resolve(request.path_info)
        except Resolver404:
            return response

        module = match.func.__module__
        in_api = module.startswith('apps.api.views')
        in_members = module.startswith('apps.members.views')
        in_auth = module.startswith('apps.authentication.views')

        if in_members or in_api:
            return response

        if in_auth and match.url_name == "fill_profile":
            return response

        if not settings.DEBUG and not request.user.is_authenticated and not in_auth:
            return redirect(reverse('login'))

        if request.user.is_authenticated and in_auth and request.method == "GET":
            return redirect(reverse('home'))

        try:
            if Profile.objects.get(user=request.user).first_access:
                return redirect(reverse('fill_profile'))
        except TypeError:
            pass

        return response
