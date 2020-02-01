FROM pennlabs/django-base

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY Pipfile* /app/

# Install project dependencies
RUN pipenv install --system

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE PennCourses.settings.production
ENV SECRET_KEY 'temporary key just to build the docker image'

# Collect static files
RUN python3 /app/manage.py collectstatic --noinput
