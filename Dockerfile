# Build React static files
FROM node:10-buster as frontend

WORKDIR /app
ENV PATH /app/node_modules/.bin:$PATH

# Install react scripts
RUN npm install react-scripts -g

# Install dependencies
COPY frontend/plan/package*.json /app/
RUN npm install

# Build static files
COPY /frontend/plan/ /app/
RUN npm run build


# Production image
FROM pennlabs/django-base

COPY --from=frontend /app/build/ /app/frontend/build/
