import json
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def receive(request):
    body_unicode = request.body.decode('utf-8')
    body_data = json.loads(body_unicode)

    headers = {key: value for key, value in request.headers.items()}

    post_params = request.POST.dict()

    response_data = {
        'body': body_data,
        'headers': headers,
        'params': post_params,
    }

    print(response_data)

    return redirect('home')
