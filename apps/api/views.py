import json
from django.views.decorators.csrf import csrf_exempt
from decouple import config
from core.settings import ALLOWED_HOSTS
from django.http import HttpResponse
from apps.home.models import Meeting, Task
from datetime import datetime
from django.contrib.auth.models import User


@csrf_exempt
def receive(request):
    if request.method == 'POST':
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)

        headers = {key: value for key, value in request.headers.items()}

        webhook_host = headers.get('Host', None)
        webhook_trigger = body_data.get('trigger', None)
        post_webhook_name = headers.get('X-Read-Webhook-Name', None)
        config_webhook_name = config('WEBHOOK_MEETING_NAME', default='YOUR-WEBHOOK-NAME')

        validations = [
            webhook_host in ALLOWED_HOSTS,
            webhook_trigger == 'meeting_end',
            post_webhook_name == config_webhook_name
        ]

        if all(validations):

            try:
                start = datetime.strptime(body_data['start_time'], '%Y-%m-%dT%H:%M:%S%z')
                end = datetime.strptime(body_data['end_time'], '%Y-%m-%dT%H:%M:%S%z')
            except ValueError:
                try:
                    start = datetime.strptime(body_data['start_time'], '%Y-%m-%dT%H:%M:%S.%f%z')
                    end = datetime.strptime(body_data['end_time'], '%Y-%m-%dT%H:%M:%S.%f%z')
                except ValueError:
                    start, end = None, None

            try:
                owner = User.objects.get(username=body_data['owner']['email'])
                external_owner = ''
            except User.DoesNotExist:
                owner = None
                external_owner = body_data['owner']['email']

            collaborators = [
                collaborator['email'] for collaborator in body_data.get('participants') if
                str(collaborator['email']).endswith('@infinitefoundry.com')
            ]

            external = [
                collaborator['email'] for collaborator in body_data.get('participants') if not
                str(collaborator['email']).endswith('@infinitefoundry.com') and collaborator['email'] is not None
            ]

            invited = [
                collaborator['name'] for collaborator in body_data.get('participants') if
                collaborator['email'] is None
            ]

            meeting = Meeting.objects.create(
                title=body_data['title'],
                start=start,
                end=end,
                owner=owner,
                external_owner=external_owner,
                external_participants=external,
                invited_participants=invited,
                summary=body_data['summary'],
                topics=body_data['topics'],
                questions=body_data['key_questions'],
                url=body_data['report_url']
            )

            meeting.participants.set(User.objects.filter(username__in=collaborators))

            meeting.save()

            for task in body_data['action_items']:
                Task.objects.create(
                    meeting=meeting,
                    title=task['text'],
                    created_by=None,
                )

            print('Meeting created successfully!')

            return HttpResponse(status=200)

        else:
            return HttpResponse(status=403)

    else:
        return HttpResponse(status=404)
