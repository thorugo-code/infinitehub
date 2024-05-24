from django.urls import resolve, reverse
from django.shortcuts import redirect
from core.settings import DEBUG


class SessionExpiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        in_members = resolve(request.path).func.__module__.startswith('apps.members.views')
        in_auth = resolve(request.path).func.__module__.startswith('apps.authentication.views')

        if in_members:
            return response
        elif not DEBUG and not request.user.is_authenticated and not in_auth:
            return redirect(reverse('login'))
        elif request.user.is_authenticated and in_auth:
            return redirect(reverse('home'))

        return response
