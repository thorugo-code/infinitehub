from django.shortcuts import redirect
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def receive(request):
    messages.info(request, 'You have successfully created a meeting')
    print(request)
    print(request.GET)
    print(request.POST)
    print(request.COOKIES)
    print(request.FILES)
    print(request.method)
    return redirect('home')
