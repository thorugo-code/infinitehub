import sqlite3
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (f'Migrate files paths in database. Run this command if you have '
            f'changed the path of the files in django settings.')

    def handle(self, *args, **options):

        # Connect to the database
        connection = sqlite3.connect('db.sqlite3')
        cursor = connection.cursor()

        # Migrate the files paths with specific paths
        # EG: tables [(table_name, column_name, old_path, new_path)]
        tables = [
            ('home_uploadedfile', 'file', 'uploads/', ''),
            ('home_profile', 'avatar', 'apps/static/assets/uploads/', ''),
            ('home_project', 'img', 'apps/static/assets/uploads/', 'project_pics/')
        ]

        for table in tables:
            cursor.execute(f'SELECT {table[1]} FROM {table[0]}')
            files = cursor.fetchall()

            for file in files:
                cursor.execute(f'UPDATE {table[0]} SET {table[1]} = ? WHERE {table[1]} = ?',
                               (file[0].replace(table[2], table[3]), file[0]))

        # Migrate the files paths of placeholder.webp
        # EG: tables [(table_name, column_name)]
        tables = [
            ('home_profile', 'avatar'),
            ('home_client', 'avatar'),
            ('home_office', 'avatar'),
            ('home_project', 'img')
        ]

        for table in tables:
            cursor.execute(f'UPDATE {table[0]} SET {table[1]} = ? WHERE {table[1]} LIKE ?',
                           ('placeholder.webp', '%placeholder.webp'))

        connection.commit()
        connection.close()
