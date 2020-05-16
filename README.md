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

## Frontend Monorepo Infrastructure

Since our frontend codebase for Penn Courses products are closely related, we've
decided to opt for a monorepo version control system to allow for easier 
code-sharing and aid future development. Currently, the `frontend/` directory 
houses 3 projects, namely `Penn Course Alert`, `Penn Course Plan` and 
`pcx-shared-components`, a library containing reusable React components/hooks 
that are used in both PCA and PCP. 

### Setting Up Development Environment 
We use [Yarn Workspaces](https://classic.yarnpkg.com/en/docs/workspaces/) 
to handle development dependency installation/resolution. In 
`frontend/package.json`, we have defined the directories of each project 
as a workspace, and running `yarn install` in `frontend/` will install 
dependencies for each project to `frontend/node_modules`. Note that currently,
both PCA and PCP have `pcx-shared-components` as a dependency as defined in 
their respective `package.json` configurations, so `yarn` will automatically 
symlink `frontend/node_modules/pcx-shared-components` to `frontend/pcx-shared-components`
and both PCA and PCP codebases can use shared components simply by 
doing `import _ from "pcx-shared-components"`. 

### Modifications to CRA 
By using Yarn Workspaces as described above, dependencies from another project 
are treated as an outside dependency, and therefore should be built and transpiled
in order to make use of them. However, having to rebuild shared dependencies 
while working on another project introduces another layer to the build process
during development, and cannot make use of hot-reloading directly. Therefore, 
we opted to modify CRA default Babel configurations to include all projects 
defined in the Yarn Workspace during transpilation, making it possible for 
hot-reloading set up in CRA to work as usual, even for editing code from 
another project that is set up as a dependency. 

There are however some caveats. This makes use of `react-app-rewired`
and `customize-cra`, which come with warnings that using these 
packages will "break the guarantees that CRA provides" and 
"no support will be provided". This will no longer be 
a concern when we move to `next.js`, since they support custom Webpack
configurations out of the box. We also use `get-yarn-workspaces` 
in our Babel configurations to automatically include all projects 
defined in our Yarn Workspace as transpilation sources.

### Pre-commit Hooks
To ensure our code base is consistent and adheres to good style, 
we also set up a pre-commit hook using `husky` to run 
Prettier and ESLint on all staged Javascript files. This makes
use of `lint-staged`. Note that a commit will not succeed if 
it does not pass ESLint. It is important to note that 
`eslint-disable next-line` might not work as intended sometimes, 
since Prettier might reformat code such that the offending line
is no longer directly below the ESLint hint. One can avoid this 
issue by using `eslint-disable` and `eslint-enable` for 
a block of code instead. 

Pre-commit hooks are executed by `lerna`, which runs the 
script `precommit` in each workspace defined in their 
respective `package.json` configurations. These scripts 
all use `lint-staged`, which are configured in 
`.lintstagedrc.yml`.




