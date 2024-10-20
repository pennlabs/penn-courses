Welcome to the Penn Courses Backend (PCX)!

## Setting up Your Development Environment

### Prerequisites

Our default mode of running PCx backend is through using Dev Containers, outlined in `penn-courses/README.md`. Follow the steps outlined there for ensuring your container gets initialized properly, then proceed with the following steps.

### Running the Backend with Docker-Compose

1. `cd backend`
2. Running Docker
   1. Open a new terminal window (also in the `backend` directory) and run `docker-compose up`
      > :warning: The default behavior of our Dev Container is for the docker daemon to be running automatically. However, if this is not the case (ie, if you cannot get `docker-compose up` to work due to a Docker connection error), or you get some Docker error along the lines of 
      > - NEED TO FIND FIX
3. Set up Django Development Environment
   1. `pipenv install --dev` – Downloads necessary packages.
   2. `pipenv shell` – Enters virtual environment for development.
   3. `python manage.py makemigrations` – Creates files that correspond with Model changes.
   4. `python manage.py migrate` – Applies migration files to database (requires running database).
   5. `python manage.py test` – Run test suite.
   6. `python manage.py test tests.review.test_api.OneReviewTestCase.test_course` – Run a specific test, or a set of tests by specifying a prefix path (e.g. `tests.review.test_api`).
4. Load test data into DB, following steps in [Loading Courses Data](#loading-courses-data).
5. Run the backend server.
   - Run the backend in development mode with the command `python manage.py runserver`. This will start the server at port `8000`.
   - Once the server is running, you can access the admin console at `localhost:8000/admin`, browse auto-generated API documentation from the code on your branch at `localhost:8000/api/documentation`, or use any of the other routes supported by this backend (comprehensively described by the API documentation), usually of the form `localhost:8000/api/...`
     
      > :warning: NOTE: if you don't need documentation specific to your branch, it is usually more convenient to browse the API docs at [penncoursereview.com/api/documentation](https://penncoursereview.com/api/documentation)
   - With the backend server running, you can also run the frontend for any of our PCX products by following the instructions in the `frontend` README.
     
      > :warning: NOTE: If you have not loaded the test data from the previous step (Step 4), ensure that you have created a local user named "Penn-Courses" with the password "postgres" in your PostgreSQL. To add the user, navigate to your pgAdmin, and follow the path of Object -> Create -> Login/Group Role and create the appropriate user.
      
      > :warning: NOTE: If you ever encounter a `pg_hba.conf` entry error, open the `~/var/lib/postgresql/data/pg_hba.conf` file in your docker container and append the line `host  all  all 0.0.0.0/0 md5` into the file.

**If you're a frontend developer** you'll want to use #5 from now on (only re-running #2 or #1 when you see a problem)

**If you're a backend developer** you'll often want to rerun #3 and #5, in the case that you are making DB changes, etc.

> *If you don't want to use a Dev Container, see the [Running the Backend Natively](#running-the-backend-natively) section. You might want to do this if, for example, you really like your local shell set up.*


## Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to
put in your `backend` directory. This will contain some sensitive credentials (which is why the file contents are not pasted in this public README). If you are not in Penn Labs, see the "Loading Course Data on Demand" section below for instructions on how to get your own credentials.

NOTE: when using `pipenv`, environment variables are only refreshed when you exit your shell and rerun `pipenv shell` (this is a common source of confusing behavior, so it's good to know about).

## Linting

We use `black`, `flake8`, and 'isort' to lint our code. Once you are in the `backend` directory, you can run the following commands to lint:
1. `pipenv run black`
2. `pipenv run isort`
3. `pipenv run flake8`

## Loading Courses Data 

### Via Database Dump (Penn Labs members)

- To get going quickly with a local database loaded with lots of test data,
   you can download this [pcx_test.sql](https://penn-labs.slack.com/files/U02FND52FLJ/F06GLQP0UF2/pcx_test_1_2024.sql) SQL dump file. You will only be able to access this if you are a member of labs; if you still need access to data, read on.
- First you'll need to install `psql` (see [Prerequisites](#prerequisites))
- Clear the existing contents of your local database with `psql template1 -c 'drop database postgres;' -h localhost -U penn-courses` (the password is `postgres`)
- Create a new database with `psql template1 -c 'create database postgres with owner "penn-courses";' -h localhost -U penn-courses` (same password).
   
   > :warning: NOTE: If this is giving you permission denied, try running `psql template1` and enter the following query `CREATE DATABASE postgres WITH OWNER "penn-courses"`.
- Finally, run `psql -h localhost -d postgres -U penn-courses -f pcx_test.sql` (replacing `pcx_test.sql` with the full path to that file on your computer) to load
   the contents of the test database (this might take a while).
- For accessing the Django admin site, the admin username is `admin` and the password is `admin` if you use this test db.


### On Demand

PCX gets its data from two primary sources: the Penn Registrar for the
current semester's data (via the [OpenData API](https://app.swaggerhub.com/apis-docs/UPennISC/open-data/prod)),
and ISC data dumps containing review statistics (from Terry Weber, [weberte@isc.upenn.edu](mailto:weberte@isc.upenn.edu)).

#### API Credentials

Interacting with the OpenData API requires credentials, `OPEN_DATA_CLIENT_ID` (`CLIENT-ID`) and `OPEN_DATA_OIDC_SECRET` (`OIDC-SECRET`). These credentials are already included in the .env file you should receive from a team lead if you are in Labs. Otherwise, you can register for prod OpenData API credentials [here](https://hosted.apps.upenn.edu/PennOpenshiftCommandCenter_UI/PublicRestAccounts.aspx).

#### Exploring the OpenData API via Postman

While the OpenData API docs are OK, sometimes it's easiest to explore the data via requests to the API (although if you want to explore PCX data specifically, I recommend using the Django admin console, available at e.g. [penncoursereview.com/admin](https://penncoursereview.com/admin)).

OpenData uses [OAuth2](https://oauth.net/2/) for authentication (I highly recommend the official video course on OAuth2 for anyone interested in better understanding this industry-standard authentication flow - this is also the basis of the [auth flow](https://penncoursereview.com/api/documentation/#section/Authentication) used by Labs / PCX apps). Specifically, OpenData uses [client credentials](https://aaronparecki.com/oauth-2-simplified/#client-credentials) as its OAuth2 "grant type" (this is pretty standard for server-to-server/userless API access). Basically, this means you need to use your client credentials (client ID / secret) to get a temporary "access token" from the authorization server.

To receive an access token, you can send a POST request to `https://sso.apps.k8s.upenn.edu/auth/realms/master/protocol/openid-connect/token` (or whatever your `OIDC-TOKEN-URL` is, if you registered for your own credentials). The body should be x-www-form-urlencoded with the key/value pairs:
   - `grant_type`: `client_credentials`
   - `client_id`: `YOUR_CLIENT_ID`
   - `client_secret`: `YOUR_CLIENT_SECRET`

You then can make authenticated requests to the API by providing a request header of the form key/value: `Authorization`: `Bearer ACCESS_TOKEN` (where `ACCESS_TOKEN` is the token you received from the authorization server).

See [courses/registrar.py](https://github.com/pennlabs/penn-courses/blob/master/backend/courses/registrar.py) to understand which OpenData API endpoints are used by PCX, and how.

For example, you can try out: `https://3scale-public-prod-open-data.apps.k8s.upenn.edu/api/v1/course_section_search?section_id=CIS&term=202410&page_number=1&number_of_results_per_page=100` (remember to set the `Authorization` header).

#### Registrar

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

#### ISC Review Data

The ISC import script has a lot of options depending on what exactly you want to do.
It can import all historical data, or just data from a specific semester. It can use
a zip file or an unzipped directory. Run `./manage.py iscimport --help` for all the
options.

If you have an ISC data dump in a ZIP format and want to import the most recent semester's (e.g. 2022A)
data, run `./manage.py iscimport --current --semester 2022A path/to/dump.zip`.

You'll be prompted for confirmation at different times in the script. If you want to skip these
prompts, add the `--force` flag.

# Appendix

## Running the Backend Natively

If you don't want to develop within a Docker container, you can also choose to run the dev environment natively.

### Prerequisites
- Python 3.11 ([`pyenv`](https://github.com/pyenv/pyenv) is recommended)
- [`pipenv`](https://pipenv.pypa.io/en/latest/)
- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)

1. `cd backend`
2. Compiling postgres (`psycopg2`)

   - **Mac**
     > :warning: NOTE: If your computer runs on Apple silicon and you use Rosetta to run Python as an x86 program, use `arch -x86_64 brew <rest of command>` for all `brew` commands.

     1. `brew install postgresql`
     2. `brew install openssl`
     3. `brew unlink openssl && brew link openssl --force`
     4. Follow the instructions printed by the previous command to add openssl to your PATH and export flags for compilers, e.g.:
        - `echo 'export PATH="/usr/local/opt/openssl@3/bin:$PATH"' >> ~/.zshrc`
        - `export LDFLAGS="-L/usr/local/opt/openssl@3/lib"`
        - `export CPPFLAGS="-I/usr/local/opt/openssl@3/include"`

   - **Windows (WSL) or Linux:**
     - `apt-get install gcc python3-dev libpq-dev`

3. Follow steps #3 onwards in the [Running the Backend with Docker-Compose](#running-the-backend-with-docker-compose) section.