FROM pennlabs/django-base:11d476546bd11c7a499e0e93be8db6af035d360f-3.11

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY pyproject.toml uv.lock /app/

# Install project dependencies
RUN uv sync --frozen --no-dev --no-install-project --python $(which python); \
    ln -s /app/.venv/bin/uwsgi /usr/local/bin/uwsgi; \
    ln -s /app/.venv/bin/gunicorn /usr/local/bin/gunicorn

# Make installed binaries available for POSIX compliant scripts
ENV PATH="/app/.venv/bin:$PATH"

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE PennCourses.settings.production
ENV SECRET_KEY 'temporary key just to build the docker image'

COPY ./scripts/asgi-run /usr/local/bin/

# Collect static files
RUN python3 /app/manage.py collectstatic --noinput
