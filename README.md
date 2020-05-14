# Penn Courses
[![CircleCI](https://circleci.com/gh/pennlabs/penn-courses.svg?style=shield)](https://circleci.com/gh/pennlabs/penn-courses)
[![Coverage Status](https://codecov.io/gh/pennlabs/penn-courses/branch/master/graph/badge.svg)](https://codecov.io/gh/pennlabs/penn-courses)

This is the (eventual) unified home of all Penn Courses products.
Currently, products contained in here include:
- Penn Courses API
- Penn Course Plan
- Penn Course Alert

## Installation
Make sure you have [`pipenv`](https://docs.pipenv.org/en/latest/) installed.

### Setting up the Django Backend
1. `git clone git@github.com:pennlabs/penn-courses.git`
2. `pipenv install`
    - You may run into some issues installing the mysql python driver on
    macOS. The development environment will use sqlite3 as the database
    by default, so this is not something to worry about.
    - However, if you do want to run locally with the production database,
    then run:
        1. `brew install openssl`
        2. `LDFLAGS=-L/usr/local/opt/openssl/lib pip install mysqlclient`
3. `pipenv shell` to activate the virtual environment
4. `python manage.py migrate`
5. Make sure everything works by running `python manage.py test` and
ensuring all tests pass.

### Setting up the the frontends
Make sure you have `nodejs` installed, which will also install `npm`
along with it. Current frontend directories are `frontend/plan` and `frontend/alert`.
1. `cd frontend/<>`
2. `npm install`

## Run in development
Make sure you're in the base directory of the project.

To run the backend server, run

`pipenv run python manage.py runserver 8000`

To run a frontend development server (for example, Penn Course Plan),
1. `cd frontend/<>`
2. `npm start`

The local version of the site should open in your default browser, and
as long as the back-end is running on port 8000, requests will be
proxied between the two development servers.

## Loading Course Data

`python manage.py setoption SEMESTER <semester>`

Where `<semester>` is something in the form of `2019C`, for Fall 2019.
Spring, Summer and Fall are `A`, `B` and `C`, respectively.

This project isn't too useful without Penn course data. To load in
course data, set the environment variables `API_KEY` and `API_SECRET` to
the `Bearer` and `Token` credentials, respectively, that you recieve
from the Penn OpenData API when you register for an API key. After those
have been set, run

`python manage.py loadcourses --semester=<semester> --query=<query>`

Let `semester` be the desired semester (for example, `2019C` represents
Fall 2019), and let query be the prefix of all courses you would like to
load in. If you're just interested in the CIS department, put `CIS`. If
you'd like to load in **ALL** courses, omit the query parameter. Note
that this will take a long time, as all sections in Penn's course catalog,
along with rooms, buildings, and instructors will be loaded in.

## Handling shared components

There are several shared components between PCA and PCP, which are located in
 `frontend/shared-components`. In order for linting of the shared components to work 
 properly, run `npm install` within the `frontend/shared-components` directory.
 This will automatically allow `frontend/shared-components` to be linted when
 either PCP or PCA is linted. `npm start` and `npm run build` in the frontend
 for either project will already sync the shared components with the actual
 projects. However, the project files corresponding with the shared components
 will not live update unless you run `npm run sync-shared-components` in the
 frontend project you're working on.
