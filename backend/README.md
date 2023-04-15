Welcome to the Penn Courses Backend (PCX)!

## Setting up Your Development Environment

### Prerequisites

- Python 3.10 ([`pyenv`](https://github.com/pyenv/pyenv) is recommended)
- [`pipenv`](https://pipenv.pypa.io/en/latest/)
- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)
- Python 3.10 ([`pyenv`](https://github.com/pyenv/pyenv) is recommended)
- [`pipenv`](https://pipenv.pypa.io/en/latest/)
- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)

### Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to
put in your `backend` directory. This will contain some sensitive credentials (which is why the file contents are not
pasted in this public README). If you are not in Penn Labs, see the "Loading Course Data on Demand" section below for instructions on how to get your own credentials.

NOTE: when using `pipenv`, environment variables are only refreshed when you exit your shell and rerun `pipenv shell` (this is a common source of confusing behavior, so it's good to know about).

### Setting Up the Backend

1. `cd backend`
2. Compiling postgres (`psycopg2`)

   - **Mac**

     > :warning: NOTE: If you are having trouble installing packages (e.g. on Apple silicon), you can use the workaround described in the next section ([Trouble Installing Packages (Apple Silicon)](#trouble-installing-packages-apple-silicon)) to run the server in a docker container.

     > :warning: NOTE: If your computer runs on Apple silicon and you use Rosetta to run Python as an x86 program, use `arch -x86_64 brew <rest of command>` for all `brew` commands.

     1. `brew install postgresql`
     2. `brew install openssl`
     3. `brew unlink openssl && brew link openssl --force`
     4. Follow the instructions printed by the previous command to add openssl to your PATH and export flags for compilers, e.g.:
        - `echo 'export PATH="/usr/local/opt/openssl@3/bin:$PATH"' >> ~/.zshrc`
        - `export LDFLAGS="-L/usr/local/opt/openssl@3/lib"`
        - `export CPPFLAGS="-I/usr/local/opt/openssl@3/include"`

   - Windows (WSL) or Linux:
     - `apt-get install gcc python3-dev libpq-dev`

3. Running Docker
   1. Open a new terminal window (also in the `backend` directory) and run `docker-compose up`
      > :warning: Depending on your system configuration, you may have to start `docker` manually. If this is the case (ie, if you cannot get `docker-compose up` to work due to a docker connection error) try this:
      >
      > - (linux) `[sudo] systemctl start docker`
      > - (WSL) `[sudo] service docker start`

> ⚠️ **NOTE** If you are having trouble installing packages or with installing pipenv (e.g., on Apple silicon), see [Trouble Installing Packages (Apple Silicon)](#trouble-installing-packages-apple-silicon). Return to finish these instructions from step 4.

4. Setting up your Penn Courses development environment

   1. `pipenv install --dev`
   2. `pipenv shell`
   3. `python manage.py migrate`

5. Loading test data (if you are a member of Penn Labs). If you are not a member of Penn Labs, you can skip this section and load in course data from the registrar, as explained below.

   - To get going quickly with a local database loaded with lots of test data,
     you can download this [pcx_test.sql](https://files.slack.com/files-pri/T4EM1119V-F04FPSTNF46/download/pcx_test_12_2022.sql)
     SQL dump file.
   - Clear the existing contents of your local database with `psql template1 -c 'drop database postgres;' -h localhost -U penn-courses` (the password is `postgres`)
   - Create a new database with `psql template1 -c 'create database postgres with owner "penn-courses";' -h localhost -U penn-courses` (same password).
   - Finally, run `psql -h localhost -d postgres -U penn-courses -f pcx_test.sql` (replacing `pcx_test.sql` with the full path to that file on your computer) to load
     the contents of the test database (this might take a while).
   - For accessing the Django admin site, the admin username is `admin` and the password is `admin` if you use this test db.
   - Run `python manage.py migrate` to apply migrations

6. Running the backend

   - Run the backend in development mode with the command `python manage.py runserver`. This will start the server at port `8000`.
   - Once the server is running, you can access the admin console at `localhost:8000/admin`, browse auto-generated API documentation from the code on your branch at `localhost:8000/api/documentation`, or use any of the other routes supported by this backend (comprehensively described by the API documentation), usually of the form `localhost:8000/api/...`
   - Note: if you don't need documentation specific to your branch, it is usually more convenient to browse the API docs at [penncoursereview.com/api/documentation](https://penncoursereview.com/api/documentation)
   - With the backend server running, you can also run the frontend for any of our PCX products by following the instructions in the `frontend` README.
   - Note: If you have not loaded the test data from the previous step (Step 4), ensure that you have created a local user named "Penn-Courses" with the password "postgres" in your PostgreSQL. To add the user, navigate to your pgAdmin, and follow the path of Object -> Create -> Login/Group Role and create the appropriate user.
   - Note: If you ever encounter a `pg_hba.conf` entry error, open the `~/var/lib/postgresql/data/pg_hba.conf` file in your docker container and append the line `host  all  all 0.0.0.0/0 md5` into the file.

7. Running tests
8. Running tests
   - Run `python manage.py test` to run our test suite.
   - To run a specific test, you can use the format `python manage.py test tests.review.test_api.OneReviewTestCase.test_course` (also note that in this example, you can use any prefix of that path to run a larger set of tests).

### Trouble Installing Packages (Apple Silicon)

1. Always run `docker-compose --profile=dev up` instead of just `docker-compose up`.
   - To alias this command, run `echo "alias courses-compose='cd "$PWD"; docker-compose up'" >> ~/.zshrc; source ~/.zshrc` (replacing `~/.zshrc` with `~/.bashrc` or whatever configuration file your shell uses, if you don't use zsh).
   - This will spin up a container from which you can run the server (with all required packages preinstalled).
2. In a separate terminal (from any directory), run `docker exec -it backend-development-1 /bin/bash` to open a shell in the container (if this says "no such container", run `docker container ls` and use the name of whatever container most closely matches the `backend_development` image). Just like exiting a Pipenv shell, you can exit the container by pressing `Ctrl+D` (which sends the "end of transmission" / EOF character).
   - You might want to add an alias for this command so it is easier to run (e.g. `echo 'alias courses-backend="docker exec -it backend_development_1 /bin/bash"' >> ~/.zshrc && source ~/.zshrc`). Then you can just run `courses-backend` from any directory to connect to the Docker container from which you will run the server (assuming `courses-compose` is already running in another terminal).
3. Once you have a shell open in the container, you can continue running the rest of the commands in this README (except you can skip `pipenv install --dev` since that has already been done for you).
   1. Remember to run `pipenv shell` (to open a [Pipenv] shell inside of a [docker container] shell inside of your computer's shell!). Note that the `/backend` directory inside the container is automatically synced with the `backend` directory on your host machine (from which you ran `docker-compose --profile=dev up`).
4. There's just one last complication. Due to some annoying details of Docker networking, you have to expose the server on IP address `0.0.0.0` inside the container, rather than `127.0.0.1` or `localhost` as is default (otherwise the server won't be accessible from outside of the container). To do this, instead of running `python manage.py runserver`, run `python manage.py runserver 0.0.0.0:8000`. In `Dockerfile.dev`, we automatically alias the command `runserver` to the latter, so in the container shell (in `/backend`, as is default) you can simply run the command `runserver` (no `python manage.py` necessary).

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
