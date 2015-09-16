#!/bin/bash
rm -f db.sqlite3
rm -f review/migrations/0*.*
python manage.py makemigrations review
python manage.py migrate
python manage.py createsuperuser --user admin --email admin@example.com
python manage.py runserver
