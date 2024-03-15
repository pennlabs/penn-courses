FROM node:10-buster as build-deps

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY degree-plan/package.json /app/degree-plan/
COPY shared-components/package.json /app/shared-components/

# Install dependencies
RUN yarn workspace penndegreeplan install --production --frozen-lockfile
RUN yarn workspace pcx-shared-components install --production --frozen-lockfile

# Copy project
COPY degree-plan/ /app/degree-plan
COPY shared-components/ /app/shared-components

# Build project
WORKDIR /app/degree-plan
RUN yarn build

FROM nginx:1.12

LABEL maintainer="Penn Labs"

COPY review/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-deps /app/degree-plan/build/ /usr/share/nginx/html
