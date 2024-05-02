import sqlite3
from django.core.management.base import BaseCommand
from django.contrib.sessions.models import Session


class Command(BaseCommand):
    help = (f'Migrate files paths in database. Run this command if you have '
            f'changed the path of the files in django settings.')

    def handle(self, *args, **options):

        # Connect to the database
        connection = sqlite3.connect('db.sqlite3')
        cursor = connection.cursor()

        # query = 'SELECT * FROM authentication_authemail'
        # cursor.execute(query)
        #
        # emails = cursor.fetchall()
        # print(emails)

        query = 'DELETE FROM authentication_authemail'
        cursor.execute(query)
        connection.commit()
        for session in Session.objects.all():
            session.delete()

            # user_id = email[1]
            # auth_token = email[2]
            # auth_key = email[3]
            # is_confirmed = email[4]
            # created_at = email[5]
            # confirmed_at = email[6]

            # query = (f'UPDATE authentication_authemail '
            #          f'SET user_id = {user_id}, '
            #          f'auth_token = "{auth_token}", '
            #          f'auth_key = "{auth_key}", '
            #          f'is_confirmed = {is_confirmed}, '
            #          f'created_at = "{created_at}", '
            #          f'confirmed_at = "{confirmed_at}" '
            #          f'WHERE user_id = {user_id}')

            # cursor.execute(query)
            # connection.commit()
