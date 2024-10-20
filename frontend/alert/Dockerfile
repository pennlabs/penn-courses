FROM node:18-bookworm

LABEL maintainer="Penn Labs"

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY alert/package.json /app/alert/
COPY shared-components/package.json /app/shared-components/

# Install dependencies
RUN yarn workspace penncoursealert install --production --frozen-lockfile
RUN yarn workspace pcx-shared-components install --production --frozen-lockfile

# Copy project
COPY alert/ /app/alert
COPY shared-components/ /app/shared-components

# Disable next telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build project
WORKDIR /app/alert
RUN yarn build

CMD ["yarn", "start"]
