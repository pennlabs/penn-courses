Welcome to the Penn Courses Backend (PCX)!

## Setting up Your Development Environment

### Prerequisites

We develop the PCX backend primarily within Dev Containers. Follow the steps outlined in `penn-courses/README.md` to ensure your container gets initialized properly, then proceed with the following steps.

If you don't want to develop in Dev Container, see the [Running the Backend Natively](#running-the-backend-natively) section. You might want to do this if, for example, you really like your local set up.

### Running the Backend with Docker-Compose

1. `cd backend`

2. Running Docker
   1. Open a new terminal window (also in the `backend` directory) and run `docker compose up`
   
      > :warning: Dev Containers should be automatically running the docker daemon. However, if this is not the case (e.g. you're facing Docker connection errors or seeing `unable to start container process` errors) follow the steps in [Running the Backend Natively](#running-the-backend-natively).
      
3. Set up Django Development Environment
   1. `uv run manage.py makemigrations` – Generates SQL files that propagate Django Model changes to database.
   2. `uv run manage.py migrate` – Applies migration files to database (requires a running database).
   3. `uv run manage.py test` – Run test suite.
   4. `uv run manage.py test tests.review.test_api.OneReviewTestCase.test_course` – Run a specific test, or a set of tests by specifying a prefix path (e.g. `tests.review.test_api`).

4. Load test data into DB, following steps in [Loading Courses Data](#loading-courses-data).

   > NOTE: If for some reason this is not possible, ensure that you have created a local user named "Penn-Courses" with the password "postgres" in your PostgreSQL. To add the user, navigate to your pgAdmin, and follow the path of Object -> Create -> Login/Group Role and create the appropriate user.

5. Run the backend server.
   - Run the backend in development mode with the command `uv run manage.py runserver`. This will start the server at port `8000`.
   - Once the server is running, you can access the admin console at `localhost:8000/admin`, browse auto-generated API documentation from the code on your branch at `localhost:8000/api/documentation`, or use any of the other routes supported by this backend (comprehensively described by the API documentation), usually of the form `localhost:8000/api/...`.

      > NOTE: if you don't need documentation specific to your branch, it is usually more convenient to browse the API docs at [penncoursereview.com/api/documentation](https://penncoursereview.com/api/documentation).

   - With the backend server running, you can also run the frontend for any of our PCX products by following the instructions in the `frontend` README.

      > :warning: If you ever encounter a `pg_hba.conf` entry error, open the `~/var/lib/postgresql/data/pg_hba.conf` file in your docker container and append the line `host  all  all 0.0.0.0/0 md5` into the file.

**If you're a frontend developer** you should only need to run Step 5 from now on (only re-running all steps if you see a problem).

**If you're a backend developer** you'll often want to rerun #3 and #5, in the case that you are making DB changes, installing new packages, etc.

## Environment Variables

If you are in Penn Labs, reach out to a Penn Courses team lead for a .env file to put in your `backend` directory. This will contain some sensitive credentials (which is why the file contents are not pasted in this public README). If you are not in Penn Labs, see the "Loading Course Data on Demand" section below for instructions on how to get your own credentials.

### Penn Course Chat

Penn Course Chat (`POST /api/chat/`, plus `POST /api/chat/stream/` which delivers the
same turn as Server-Sent Events; both served by the `chat` app) uses whichever supported
provider key is configured. `ANTHROPIC_API_KEY` enables the configured Claude model;
`OPENCODE_GO_API_KEY` enables OpenCode Go's DeepSeek V4.1 Flash and GLM-5.3 models. The
authenticated frontend reads `GET /api/chat/models/` and shows only those enabled models.
If neither key is set, chat returns a 503 explaining that it is unconfigured, and the rest
of the backend is unaffected. Get an Anthropic key from
[console.anthropic.com](https://console.anthropic.com/) or an OpenCode Go key from your
OpenCode account, then add it to `.env`.

Note that nothing in this project reads `.env` automatically, so adding the key to the
file is not enough on its own — you have to get it into the server's environment:

```bash
uv run --env-file .env manage.py runserver
# or, for the whole shell session:
set -a; source .env; set +a
```

These optional variables tune it (defaults in parentheses):

| Variable | Purpose |
| --- | --- |
| `CHAT_MODEL` (`claude-sonnet-5`) | Anthropic model to offer when `ANTHROPIC_API_KEY` is set. |
| `OPENCODE_GO_API_KEY` | Enables OpenCode Go's curated DeepSeek V4.1 Flash and GLM-5.3 choices. |
| `OPENCODE_GO_BASE_URL` (`https://opencode.ai/zen/go/v1`) | OpenCode Go API base URL. |
| `CHAT_DEFAULT_MODEL` (`opencode-go/deepseek-v4.1-flash`) | Preferred fully-qualified choice; falls back to an enabled model. |
| `CHAT_EFFORT` (`medium`) | Reasoning effort: `low`, `medium`, `high`, `xhigh`, `max`. Higher is slower and costs more. |
| `CHAT_MAX_TOKENS` (`4096`) | Output token cap per reply. |
| `CHAT_MAX_TOOL_TURNS` (`16`) | Round trips to the model within one message. Each carries a batch of tool calls, so this is well above 16 lookups. Bounds latency and spend per message; hitting it abandons the turn rather than returning a partial answer. |
| `CHAT_RATE_LIMIT` (`30/hour`) | Per-user rate limit on the chat route. |
| `CHAT_MAX_MESSAGES` (`40`) | Longest conversation history a client may submit. |
| `CHAT_MAX_MESSAGE_CHARS` (`4000`) | Longest single message a client may submit. |

The assistant can read and modify the requesting user's own PCP cart and schedules
(`chat/plan_tools.py`) and read their Penn Degree Plan (`chat/degree_tools.py`). Those
tools are the only ones handed a user, and they take it from `request.user` — no tool
schema accepts an identity, so the model cannot name one.

Search results are marked `already_taken` / `already_planned` against the student's
degree plan, cart and schedules, so the assistant does not recommend courses back to
them. Those comparisons run over crosslisting groups (`chat/student.py`): Penn lists one
class under several codes — most often an undergraduate and a graduate number, like
CIS-4480 and CIS-5480 — and PCX models that with `Course.primary_listing`, so a student
who took one has taken the other. The alternate codes also come back as
`also_listed_as` from `get_course` and from the degree plan.

A degree's rule tree is far too large to hand over whole, so `get_my_degree_plan`
collapses satisfied branches to one line and expands only what is outstanding. Each
unmet leaf carries its rule id, which `search_courses` accepts as `rule_ids` — that is
what turns "what do I still need" into "here is what to take for it", using the same
`degree_rules_filter` Penn Degree Plan search uses.
Writes read the schedule back from the database afterwards and report what is
verifiably there (`confirmed_in_schedule`) alongside anything that did not land
(`failed_to_add` / `failed_to_remove`), so the assistant describes the result of a
change rather than the request it made.

Writes are additive: they never delete a schedule, they refuse the reserved
`Path Registration` schedule as PCP's own API does, and they cap how many sections one
call may touch. They also refuse a section with no published meeting times unless
explicitly told otherwise — such a section cannot be checked for conflicts and does not
draw on PCP's calendar, so adding one has to be the student's decision rather than a
side effect.

## Linting

We use `black`, `flake8`, and 'isort' to lint our code. Once you are in the `backend` directory, you can run the following commands to lint:
1. `uv run black`
2. `uv run isort`
3. `uv run flake8`

Please try to run these commands before committing your code – CI checks will fail when your code isn't properly linted.

## Loading Courses Data 

### Via Database Dump (Penn Labs members)

- To get going quickly with a local database loaded with lots of test data, you can download this [pcx_test.sql](https://penn-labs.slack.com/files/U04NPQQ2WRF/F07SHJSUKHT/pcx_test_10_2024.sql.zip) SQL dump file. You will only be able to access this if you are a member of Labs; if you still need access to data, read on.
- Clear the existing contents of your local database with `psql template1 -c 'drop database postgres;' -h localhost -U penn-courses` (the password is `postgres`).
- Create a new database with `psql template1 -c 'create database postgres with owner "penn-courses";' -h localhost -U penn-courses` (same password).
   
   > :warning: If this is giving you permission denied, try running `psql template1` and enter the following query `CREATE DATABASE postgres WITH OWNER "penn-courses"`.

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
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
- [`docker` and `docker-compose`](https://docs.docker.com/get-docker/)
- Postgres Server (`psycopg2`)

   - **Mac**
     > NOTE: If your computer runs on Apple silicon and you use Rosetta to run Python as an x86 program, use `arch -x86_64 brew <rest of command>` for all `brew` commands.

     1. `brew install postgresql`
     2. `brew install openssl`
     3. `brew unlink openssl && brew link openssl --force`
     4. Follow the instructions printed by the previous command to add openssl to your PATH and export flags for compilers, e.g.:
        - `echo 'export PATH="/usr/local/opt/openssl@3/bin:$PATH"' >> ~/.zshrc`
        - `export LDFLAGS="-L/usr/local/opt/openssl@3/lib"`
        - `export CPPFLAGS="-I/usr/local/opt/openssl@3/include"`

   - **Windows (WSL) or Linux:**
     - `apt-get install gcc uv libpq-dev postgresql-client`

### Running the Backend
Follow steps from #3 onwards in the [Running the Backend with Docker-Compose](#running-the-backend-with-docker-compose) section.
