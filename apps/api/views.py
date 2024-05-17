from django.shortcuts import redirect
from django.contrib import messages


def receive(request):
    messages.info(request, 'You have successfully created a meeting')
    print(request)
    print(request.GET)
    print(request.POST)
    print(request.COOKIES)
    print(request.FILES)
    print(request.method)
    return redirect('home')
