del db.sqlite3
del review\migrations\0*.*
python3 manage.py makemigrations review
python3 manage.py migrate
rem python3 manage.py createsuperuser --user admin --email admin@example.com
python3 manage.py runserver
