# Penn Courses

This is the (eventual) unified home of all Penn Courses products.
Currently, products contained in here include:
- Penn Courses API
- Penn Course Plan

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

### Setting up the Penn Course Plan Frontend
Make sure you have `nodejs` installed, which will also install `npm`
along with it.
1. `cd frontend/plan`
2. `npm install`

## Run in development
Make sure you're in the base directory of the project.

To run the backend server, run

`pipenv run python manage.py runserver 8000`

To run a frontend development server (for example, Penn Course Plan),
1. `cd frontend/plan`
2. `npm start`

The local version of the site should open in your default browser, and
as long as the back-end is running on port 8000, requests will be
proxied between the two development servers.
