Welcome to the Penn Courses Backend (PCX)!

## Setting up Your Development Environment

### Prerequisites

- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)
- `psql` (usually packaged as `postgresql-client`)

### Running the Backend with Docker-Compose

1. Build the docker image (the `[sudo]` part means try running without sudo first)
```sh
cd backend
[sudo] docker-compose down
[sudo] docker-compose build --no-cache development
```
> :warning: Depending on your system configuration, you may have to start `docker` manually. If this is the case (ie, if you cannot get `docker-compose run` to work due to a docker connection error) try this:
>
> - linux `[sudo] systemctl start docker`
> - WSL `[sudo] service docker start`
2. Run shell inside the container
```sh
[sudo] docker-compose run --service-ports development /bin/bash # launch shell inside container
pipenv shell # activate shell with python packages
python manage.py makemigrations
python manage.py migrate # database migrations
python manage.py test # run tests
python manage.py test tests.review.test_api.OneReviewTestCase.test_course # re-run a specific test
runserver # optionally, run the server from within the shell
exit # leave pipenv shell 
exit # leave docker shell
```
3. Run the server on `127.0.0.1:8000` (use `CTRL+C` to stop running this)
```
[sudo] docker-compose --profile dev up
```

**If you're a frontend developer** you'll want to use #2 from now on (only re-running #2 or #1 when you see a problem)

**If you're a backend developer** you'll often want to open the shell as we did in #2 (you'll only need to re-run #1 if you see a problem).

> *If you want to run the backend natively (ie, outside of docker-compose), see the [Running the Backend Natively](#running-the-backend-natively) section. You might want to do this if, for example, you really like your local shell set up*

### Attaching to Docker from IDE

Many IDEs allow attachment to running docker containers, which allows for nice features like intellisense.
1. [VSCode](https://code.visualstudio.com/docs/devcontainers/attach-container)
>  1. `CTRL-SHIFT-P` and type "Attach to Running Container"
>  2. Select the `backend_development_1` container (or a similarly named one). This should open a new VSCode window attached to the container
>  3. Open the `/backend` folder within the container
2. [PyCharm](https://www.jetbrains.com/help/pycharm/using-docker-as-a-remote-interpreter.html#config-docker)


## Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to
put in your `backend` directory. This will contain some sensitive credentials (which is why the file contents are not
pasted in this public README). If you are not in Penn Labs, see the "Loading Course Data on Demand" section below for instructions on how to get your own credentials.

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

If you don't want to use docker alone, you can also set up and run the dev environment more natively.

### Prerequisites
- Python 3.11 ([`pyenv`](https://github.com/pyenv/pyenv) is recommended)
- [`pipenv`](https://pipenv.pypa.io/en/latest/)
- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)

`psql` is required to load data into the db, but it should be installed when you install `postgres`/`psycopg2`.

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

3. Running Docker
   1. Open a new terminal window (also in the `backend` directory) and run `docker-compose up`
      > :warning: Depending on your system configuration, you may have to start `docker` manually. If this is the case (ie, if you cannot get `docker-compose up` to work due to a docker connection error) try this:
      >
      > - (linux) `[sudo] systemctl start docker`
      > - (WSL) `[sudo] service docker start`

4. Setting up your Penn Courses development environment

   1. `pipenv install --dev`
   2. `pipenv shell`
   3. `python manage.py migrate`

5. Loading test data (if you are a member of Penn Labs). If you are not a member of Penn Labs, you can skip this section and load in course data from the registrar, as explained below.


6. Running the backend

   - Run the backend in development mode with the command `python manage.py runserver`. This will start the server at port `8000`.
   - Once the server is running, you can access the admin console at `localhost:8000/admin`, browse auto-generated API documentation from the code on your branch at `localhost:8000/api/documentation`, or use any of the other routes supported by this backend (comprehensively described by the API documentation), usually of the form `localhost:8000/api/...`
     
      > :warning: NOTE: if you don't need documentation specific to your branch, it is usually more convenient to browse the API docs at [penncoursereview.com/api/documentation](https://penncoursereview.com/api/documentation)
   - With the backend server running, you can also run the frontend for any of our PCX products by following the instructions in the `frontend` README.
     
      > :warning: NOTE: If you have not loaded the test data from the previous step (Step 4), ensure that you have created a local user named "Penn-Courses" with the password "postgres" in your PostgreSQL. To add the user, navigate to your pgAdmin, and follow the path of Object -> Create -> Login/Group Role and create the appropriate user.
      
      > :warning: NOTE: If you ever encounter a `pg_hba.conf` entry error, open the `~/var/lib/postgresql/data/pg_hba.conf` file in your docker container and append the line `host  all  all 0.0.0.0/0 md5` into the file.

7. Running tests
   - Run `python manage.py test` to run our test suite.
   - To run a specific test, you can use the format `python manage.py test tests.review.test_api.OneReviewTestCase.test_course` (also note that in this example, you can use any prefix of that path to run a larger set of tests).
