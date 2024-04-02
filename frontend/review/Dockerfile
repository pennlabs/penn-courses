FROM node:18-bookworm as build-deps

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY review/package.json /app/review/
COPY shared-components/package.json /app/shared-components/

# Install dependencies
RUN yarn workspace penncoursereview install --production --frozen-lockfile
RUN yarn workspace pcx-shared-components install --production --frozen-lockfile

# Copy project
COPY review/ /app/review
COPY shared-components/ /app/shared-components

# Build project
WORKDIR /app/review
RUN yarn build

FROM nginx:1.12

LABEL maintainer="Penn Labs"

COPY review/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build-deps /app/review/build/ /usr/share/nginx/html
