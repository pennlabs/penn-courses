FROM node:18-bookworm

LABEL maintainer="Penn Labs"

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY plan/package.json /app/plan/
COPY shared-components/package.json /app/shared-components/

# Install dependencies
RUN yarn workspace penncourseplan install --production --frozen-lockfile
RUN yarn workspace pcx-shared-components install --production --frozen-lockfile

# Copy project
COPY plan/ /app/plan
COPY shared-components/ /app/shared-components

# Disable next telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build project
WORKDIR /app/plan
RUN yarn build

CMD ["yarn", "start"]
