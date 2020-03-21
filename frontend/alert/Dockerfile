FROM node:10-buster as build-deps

LABEL MAINTAINER Penn Labs

WORKDIR /app/

# Copy project dependencies
COPY package*.json /app/
RUN npm install

COPY . /app/
RUN npm run build

FROM nginx:1.12
COPY --from=build-deps /app/build/ /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]