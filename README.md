# Penn Courses
![Workflow](https://github.com/pennlabs/penn-courses/workflows/Workflow/badge.svg)
[![Coverage Status](https://codecov.io/gh/pennlabs/penn-courses/branch/master/graph/badge.svg)](https://codecov.io/gh/pennlabs/penn-courses)

This is the unified home of all [Penn Courses](https://penncourses.org) products.

## Installation & Setup
1. [Install the backend](https://github.com/pennlabs/penn-courses/blob/master/backend/README.md)
2. If you need to, [install the frontend](https://github.com/pennlabs/penn-courses/blob/master/frontend/README.md)

Note that you need the backend to run the frontend.

### Using Dev Containers

This repository has a built-in dev container that you can use to develop the project. To use it, you need to have [Docker](https://www.docker.com/products/docker-desktop) and [VSCode](https://code.visualstudio.com/) installed.

Press the remote container button in the bottom left of the window and select "Reopen in Container". This will build the dev container and open the project in a new window.

This container is designed to work with both backend and frontend development. Some additional steps are required, like installing `pipenv` dependencies and setting up the database and running the frontend server. Please read and follow the instructions in the backend and frontend READMEs.

For more information, visit dev container [documentation](https://code.visualstudio.com/docs/remote/containers).

#### Pushing Code

You can use `ssh-add` to make your SSH keys available to the dev container. This will allow you to push code to GitHub.

```
ssh-add ~/.ssh/id_rsa
```




## API Documentation
API Docs can be found at `/api/documentation` on the back-end server. Also check out the code for more explanations
and documentation! We've tried to keep it up-to-date.

## Runbook
This section is to collect thoughts/learnings from the codebase that have been hard-won, so we don't lose a record of it
if and when the information proves useful again

### Derived fields
Normally, derived fields on models are represented as `@property`-decorated functions. However, there are a few in
the codebase that need to be accessed on the database layer without `JOIN`s. So that they can be indexed.
Specifically, these are the `full_code` fields on `Course` and `Section` models, which are derived from fields on related
models.

These are updated every time the `save()` method is called. However, it's possible to get into a state 
(such as with db migrations) where `full_code` isn't set properly.

Open a shell in production, and run this small script:
```python
from tqdm import tqdm
from courses.models import Section, Course

for c in tqdm(Course.objects.all().select_related("department")):
    c.save()

for s in tqdm(Section.objects.all().select_related("course")):
    s.save()
```

`tqdm` will give you a nice progress bar as the script completes. The `select_related` clause speeds up the query,
avoiding what would be a pretty nasty N+1 scenario.
