FROM pennlabs/django-base:281d2f6446bb5381e1a2ecf39f6689b648d92ee6-3.10.1

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY pyproject.toml /app/
COPY poetry.lock /app/

# Install project dependencies
RUN poetry install --no-root

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE PennCourses.settings.production
ENV SECRET_KEY 'temporary key just to build the docker image'

COPY ./scripts/asgi-run /usr/local/bin/

# Collect static files
RUN python3 /app/manage.py collectstatic --noinput
