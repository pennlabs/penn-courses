FROM pennlabs/django-base:f0f05216db7c23c1dbb5b95c3bc9e8a2603bf2fd

LABEL maintainer="Penn Labs"

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    cmake build-essential pkg-config libgoogle-perftools-dev \
    && rm -rf /var/lib/apt/lists/*

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
