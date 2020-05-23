FROM node:10-buster as build-deps

MAINTAINER Penn Labs

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY plan/ /app/plan
COPY shared-components/ /app/shared-components
RUN yarn workspace penncourseplan install
RUN yarn workspace pcx-shared-components install

# Build project
WORKDIR /app/plan
RUN yarn build

FROM nginx:1.12
COPY --from=build-deps /app/plan/build/ /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
