FROM node:10-buster as build-deps

MAINTAINER Penn Labs

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY plan/ /app/plan
COPY shared-components/ /app/shared-components
RUN yarn workspace penncourseplan install --production --frozen-lockfile
RUN yarn workspace pcx-shared-components install --production --frozen-lockfile

# Build project
WORKDIR /app/plan
RUN yarn build

CMD ["yarn", "start"]
