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
6. Run with `python manage.py runserver` and go to `localhost:8000/admin` to view the admin site!

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
