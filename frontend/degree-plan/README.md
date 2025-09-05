Welcome to Penn Degree Plan frontend!

## Setup

1. Follow steps in course backend README. After setting up the data dump, come back here.

2. Go to localhost:8000/admin and log in (username and password are admin)

3. Go to "PDP Beta Users" under DEGREE

4. Click "Add PDP Beta User" and add admin, wharton, and engineering

5. Frontend should work now!

## Troubleshooting

- When I load the frontend, I'm getting this error: TypeError: Cannot read properties of undefined (reading 'substring')
    - Make sure you've done steps 2-4! This usually happens because you forgot to authenticate the admin/wharton/engineering beta users
- I can't log into localhost:8000/admin
    - Something probably went wrong with your data dump :(. Repeat the steps in the backend README regarding loading in a data dump.
- I get this error when applying migrations: DETAIL:  Key (id)=(198) already exists. (or some other id)
    - This means the id sequence in the django_migrations table is out of sync with the actual data
    - Run this wherever you can run SQL that affects the db (I use DBeaver):
    - SELECT setval(pg_get_serial_sequence('django_migrations','id'), (SELECT MAX(id) FROM django_migrations));
- I get this error when applying migrations: django.db.utils.ProgrammingError: column "legal" of relation "degree_fulfillment" already exists
    - Something weird happened with django's migration history. Fake the migration by running this command
    - python manage.py migrate degree 0002_fulfillment_legal_fulfillment_unselected_rules_and_more --fake
- Something else?
    - Ask me or Chat idk