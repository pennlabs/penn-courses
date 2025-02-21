FROM pennlabs/django-base:b269ea1613686b1ac6370154debbb741b012de1a-3.11

LABEL maintainer="Penn Labs"

# Copy project dependencies
COPY pyproject.toml /app/
COPY uv.lock /app/

# Install dependencies
RUN apt-get update \
    && apt-get install --no-install-recommends -y curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install uv
# Download the latest installer
ADD https://astral.sh/uv/0.6.0/install.sh /uv-installer.sh

RUN echo "5464b06094b6363861b99cd60a010892e52fc2a7503b7594419828e74afecfe6  /uv-installer.sh" | sha256sum -c

# Run the installer then remove it
RUN sh /uv-installer.sh && rm /uv-installer.sh

# Ensure the installed binary is on the `PATH`
ENV PATH="/root/.local/bin/:$PATH"

# Copy project files
COPY . /app/

ENV DJANGO_SETTINGS_MODULE PennCourses.settings.production
ENV SECRET_KEY 'temporary key just to build the docker image'

COPY ./scripts/asgi-run /usr/local/bin/

# Collect static files
RUN uv run /app/manage.py collectstatic --noinput
