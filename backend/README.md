Welcome to the Penn Courses Backend (PCX)!

## Installation
Make sure you have [`pipenv`](https://docs.pipenv.org/en/latest/) installed.

## Setting up the Django Backend
1. `cd backend`
2. `pipenv install --dev`
    - You may run into some issues installing the MySQL and Postgres database drivers on
    macOS and `uwsgi` on Windows. These dependencies are not used in development,
    so don't worry about this :)
3. `pipenv shell` to activate the virtual environment
4. `python manage.py migrate`
5. Make sure everything works by running `python manage.py test` and
ensuring all tests pass.
6. Create an admin user with `python manage.py createsuperuser`
7. Run with `python manage.py runserver` and go to `localhost:8000/admin`, login with your
   new user to make sure the site backend operational!

## Set the proper semester
PCA and PCP rely on the semester being set properly to work.

`python manage.py setoption SEMESTER <semester>`

Where `<semester>` is something in the form of `2019C`, for Fall 2019.
Spring, Summer and Fall are `A`, `B` and `C`, respectively.

## Loading Course Data
PCX gets its data from two primary sources: the Penn Registrar for the
current semester's data, and ISC data dumps containing review statistics.

### Registrar
This project isn't too useful without Penn course data. To load in
course data, set the environment variables `API_KEY` and `API_SECRET` to
the `Bearer` and `Token` credentials, respectively, that you recieve
from the Penn OpenData API when you register for an API key. After those
have been set, run

`python manage.py registrarimport --semester=<semester> --query=<query>`

Let `semester` be the desired semester (for example, `2019C` represents
Fall 2019), and let query be the prefix of all courses you would like to
load in. If you're just interested in the CIS department, put `CIS`. If
you'd like to load in **ALL** courses, omit the query parameter. Note
that this will take a long time, as all sections in Penn's course catalog,
along with rooms, buildings, and instructors will be loaded in.

### ISC Review Data
The ISC import script has a lot of options depending on what exactly you want to do.
It can import all historical data, or just data from a specific semester. It can use
a zip file or an unzipped directory. Run `./manage.py iscimport --help` for all the
options.

If you have an ISC data dump in a ZIP format and want to import the most recent semester's (e.g. 2020C)
data, run `./manage.py iscimport --current --semester 2020C path/to/dump.zip`.

You'll be prompted for confirmation at different times in the script. If you want to skip these
prompts, add the `--force` flag.


## Runbook
This section is to collect thoughts/learnings from the codebase that have been hard-won, so we don't lose a record of it
if and when the information proves useful again

### Derived fields
Normally, derived fields on models are represented as `@property`-decorated functions. However, there are a few in
the codebase that need to be accessed on the database layer without `JOIN`s. So that they can be indexed.
Specifically, these are the `full_code` fields on `Course` and `Section` models, which are derived from fields on related
models.

These are updated every time the `save()` method is called. However, it's possible to get into a state 
(such as with db migrations) where `full_code` isn't set properly.

Open a shell in production, and run this small script:
```python
from tqdm import tqdm
from courses.models import Section, Course

for c in tqdm(Course.objects.all().select_related("department")):
    c.save()

for s in tqdm(Section.objects.all().select_related("course")):
    s.save()
```

`tqdm` will give you a nice progress bar as the script completes. The `select_related` clause speeds up the query,
avoiding what would be a pretty nasty N+1 scenario.
