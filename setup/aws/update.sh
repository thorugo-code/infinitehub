#!/bin/bash

python3 manage.py migrate

python3 manage.py reset_collaborators_id

python3 manage.py update_permissions

nohup python3 manage.py runserver 0.0.0.0:8000 > output.log 2>&1 &
