FROM pennlabs/django-base:9c4f31bf1af44219d0f9019271a0033a222291c2-3.10.1

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY Pipfile* /app/

# Install project dependencies
RUN pipenv install --system --deploy


# Install system dependencies to support GeoDjango
RUN apt-get update && apt-get install -y gdal-bin libgdal-dev python3-gdal binutils libproj-dev

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE PennCourses.settings.production
ENV SECRET_KEY 'temporary key just to build the docker image'

COPY ./scripts/asgi-run /usr/local/bin/

# Collect static files
RUN python3 /app/manage.py collectstatic --noinput
