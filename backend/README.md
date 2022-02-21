Welcome to the Penn Courses Backend (PCX)!

## Installation

Make sure you have [`pipenv`](https://docs.pipenv.org/en/latest/) installed.

## Setting up the Django Backend

1. `cd backend`
2. `pipenv install --dev`
3. `pipenv shell` to activate the virtual environment
4. `python manage.py migrate`
5. Make sure everything works by running `python manage.py test` and
   ensuring all tests pass.
6. Create an admin user with `python manage.py createsuperuser`
7. Run with `python manage.py runserver` and go to `localhost:8000/admin`, login with your
   new user to make sure the site backend operational!

## Quick DB Setup

To get going quickly with a local database loaded with lots of test data,
you can download this [db.sqlite3](https://penn-labs.slack.com/files/UNUMGB11A/F02GKJ0MTDJ/db.sqlite3)
file and put it in your `backend` directory. Then you should run `python manage.py migrate`
in your `backend` directory to make sure the db schema is up-to-date with the most recent code changes.
This file is only accessible to Penn Labs members
(anyone else should sign up for a [Penn OpenData API key](https://esb.isc-seo.upenn.edu/8091/documentation#security)
and follow the steps below). You can replace the existing db.sqlite file generated from step 4 in
[Setting up the Django Backend](#setting-up-the-django-backend).
The admin username is `admin` and the password is `admin` if you use this test db
(rather than the admin username and password you created in step 6 of Setting up the Django Backend).

## Set the proper semester

PCx relies on the semester being set properly to work. You should set the current semester,
even if you are using the test database linked in [Quick DB Setup](#quick-db-setup),
because that file was created in a previous semester.

`python manage.py setoption SEMESTER <semester>`

Where `<semester>` is of the form YYYYx where x is A [for spring],
B [summer], or C [fall] (e.g. `2019C` for fall 2019).

## Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to
put in your `backend` directory. This will contain settings specific to your local
environment and some sensitive credentials (which is why the file contents are not
pasted in this public README).

## Loading Course Data

PCX gets its data from two primary sources: the Penn Registrar for the
current semester's data (via the [OpenData API](https://esb.isc-seo.upenn.edu/8091/documentation#overview)),
and ISC data dumps containing review statistics (from Terry Weber, [weberte@isc.upenn.edu](mailto:weberte@isc.upenn.edu)).

### Registrar

This project isn't too useful without Penn course data (although note that the
test database linked in [Quick DB Setup](#quick-db-setup) has course data pre-loaded).
To load in course data for a certain semester, set the environment variables
`API_KEY` and `API_SECRET` to the `Bearer` and `Token` credentials, respectively,
that you recieve from the Penn OpenData API when you register for an API key
(these credentials are already included in the .env file you should receive from a
Penn Courses team lead if you are in Labs).
After those have been set, run

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
