Welcome to the Penn Courses Backend (PCX)!

## Setting up Your Development Environment

### Prerequisites

-   Python 3.10 (`pyenv` is recommended)
-   `pipenv`
-   `docker` and `docker-compose`

### Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to
put in your `backend` directory. This will contain settings specific to your local
environment and some sensitive credentials (which is why the file contents are not
pasted in this public README).

NOTE: when using `pipenv`, environment variables are only refreshed when you exit your shell and rerun `pipenv shell` (this is a common source of confusing behavior, so it's good to know about).

### Launching the Backend

First, navigate to the `backend` directory in your terminal.

1. Initial setup for compiling `psycopg2`

    - Mac:
        - (If your computer runs on Apple silicon and you use Rosetta to run Python as an x86 program, use `arch -x86_64 brew install <package>` to install the following packages. Otherwise, run the commands as listed.)
            - `brew install postgresql`
            - `brew install openssl`
        - `brew unlink openssl && brew link openssl --force`
        - Follow the instructions printed by the previous command to add openssl to your PATH and export flags for compilers, e.g.:
            - ` echo 'export PATH="/usr/local/opt/openssl@3/bin:$PATH"' >> ~/.zshrc`
            - `export LDFLAGS="-L/usr/local/opt/openssl@3/lib"`
            - `export CPPFLAGS="-I/usr/local/opt/openssl@3/include"`
    - Windows (WSL) or Linux:
        - `apt-get install gcc python3-dev libpq-dev`

2. Running Docker

    - Run `docker-compose up` in a separate terminal window (also in the `backend` directory) before running any manage.py commands (this will spin up a Docker container running Postgres and Redis).
    - If (and only if) you are having trouble installing packages on your computer (e.g. issues installing on M1 architecture), run `docker-compose up --profile=dev` instead of just `docker-compose up`. This will spin up a container that you can ssh into to run the backend server (with all required packages preinstalled). Then in a separate terminal, you can run `docker exec -it backend_development_1 /bin/bash` (if this says no such container, try `... backend-development-1...`, and if that doesn't work then run `docker container ls` and use the name of whatever container most closely matches the `backend_development` image). You can think of this as "SSHing" into the running Docker container. Once you are in the container, you can continue running the rest of the commands in this README (skip the `pipenv install --dev` step, start with `pipenv shell`, etc.).


3. Setting up your Penn Courses development environment

    - `pipenv install --dev`
    - `pipenv shell`
    - `python manage.py migrate`

4. Loading test data (if you are a member of Penn Labs)

    - To get going quickly with a local database loaded with lots of test data,
      you can download this [pcx_test.sql](https://penn-labs.slack.com/archives/CDDK7CB53/p1650211990189289)
      SQL dump file.
      This file is only accessible to Penn Labs members (anyone else should skip this step and load in course data from the registrar, as explained below).
    - Clear the existing contents of your local database with `psql template1 -c 'drop database postgres;' -h localhost -U penn-courses` (the password is `postgres`)
    - Create a new database with `psql template1 -c 'create database postgres with owner "penn-courses";' -h localhost -U penn-courses` (same password).
    - Finally, run `psql -h localhost -d postgres -U penn-courses -f pcx_test.sql` (replacing `pcx_test.sql` with the full path to that file on your computer) to load
      the contents of the test database (this might take a while).
    - For accessing the Django admin site, the admin username is `admin` and the password is `admin` if you use this test db.

5. Running the backend

    - Run the backend in development mode with the command `python manage.py runserver`. This will start the server at port `8000`.
    - Once the server is running, you can access the admin console at `localhost:8000/admin`, browse auto-generated API documentation from the code on your branch at `localhost:8000/api/documentation`, or use any of the other routes supported by this backend (comprehensively described by the API documentation), usually of the form `localhost:8000/api/...`
    - Note: if you don't need documentation specific to your branch, it is usually more convenient to browse the API docs at [penncoursereview.com/api/documentation](https://penncoursereview.com/api/documentation)
    - With the backend server running, you can also run the frontend for any of our PCX products by following the instructions in the `frontend` README.

6. Running tests
    - Run `python manage.py test` to run our test suite.
    - To run a specific test, you can use the format `python manage.py test tests.review.test_api.OneReviewTestCase.test_course` (also note that in this example, you can use any prefix of that path to run a larger set of tests).

## Loading Course Data on Demand

PCX gets its data from two primary sources: the Penn Registrar for the
current semester's data (via the [OpenData API](https://app.swaggerhub.com/apis-docs/UPennISC/open-data/prod)),
and ISC data dumps containing review statistics (from Terry Weber, [weberte@isc.upenn.edu](mailto:weberte@isc.upenn.edu)).

### Registrar

To load in course data for a certain semester, set the environment variables
`OPEN_DATA_CLIENT_ID` and `OPEN_DATA_OIDC_SECRET` to the corresponding credentials you
receive from the OpenData API. These credentials are already included in the .env file you should receive from a team lead if you are in Labs. Otherwise, you can register for prod OpenData API credentials [here](https://hosted.apps.upenn.edu/PennOpenshiftCommandCenter_UI/PublicRestAccounts.aspx).
After your environment variables have been set (remember to refresh your pipenv shell), run

`python manage.py registrarimport --semester=<semester> --query=<query>`

Let `semester` be the desired semester (for example, `2022C` represents
Fall 2022), and let `query` be the prefix of all courses you would like to
load in (no dashes). If you're just interested in the CIS department, put `CIS`. If
you'd like to load in **ALL** courses, omit the query parameter. Note
that this will take a long time, as all sections in Penn's course catalog,
along with rooms, buildings, and instructors will be loaded in.

### ISC Review Data

The ISC import script has a lot of options depending on what exactly you want to do.
It can import all historical data, or just data from a specific semester. It can use
a zip file or an unzipped directory. Run `./manage.py iscimport --help` for all the
options.

If you have an ISC data dump in a ZIP format and want to import the most recent semester's (e.g. 2022A)
data, run `./manage.py iscimport --current --semester 2022A path/to/dump.zip`.

You'll be prompted for confirmation at different times in the script. If you want to skip these
prompts, add the `--force` flag.
