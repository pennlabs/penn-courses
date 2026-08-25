FROM node:18-bookworm

LABEL maintainer="Penn Labs"

WORKDIR /app/

# Copy project dependencies
COPY package.json /app
COPY yarn.lock /app
COPY chat/package.json /app/chat/

# Install dependencies
RUN yarn workspace penncoursechat install --production --frozen-lockfile

# Copy project
COPY chat/ /app/chat

# Disable next telemetry
ENV NEXT_TELEMETRY_DISABLED=1

# Build project
WORKDIR /app/chat
RUN yarn build

CMD ["yarn", "start"]
