FROM node:10-buster as build-deps

LABEL MAINTAINER Penn Labs

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY alert/ /app/alert
COPY shared-components/ /app/shared-components
RUN yarn workspace alert install
RUN yarn workspace pcx-shared-components install

# Build project
WORKDIR /app/alert
RUN yarn build

FROM nginx:1.12
COPY --from=build-deps /app/alert/build/ /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
