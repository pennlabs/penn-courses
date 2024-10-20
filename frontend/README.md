# Frontend Monorepo Infrastructure

Since our frontend codebase for Penn Courses products are closely related, we've
decided to opt for a monorepo version control system to allow for easier 
code-sharing and aid future development. Currently, the `frontend/` directory 
houses 3 projects, namely `Penn Course Alert`, `Penn Course Plan` and 
`pcx-shared-components`, a library containing reusable React components/hooks 
that are used in both PCA and PCP. 

## Setting Up Development Environment 
Make sure you have `node` (with a version that is ^18) and `yarn` installed.
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

## Running the frontends
To run a frontend development server,
1. `cd frontend`
2. `yarn` to ensure dependencies are up-to-date.
3. `cd [alert|plan|review]` depending on which frontend you'd like to run.
4. `yarn` once more (just to be sure `:)`)
5. `yarn dev` to run the frontend.

Feel free to leave out the `yarn`s when you know dependencies are up-to-date.

As long as the back-end is running on port 8000, requests will be
proxied between the two development servers.

## Modifications to CRA 
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

## Pre-commit Hooks
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



