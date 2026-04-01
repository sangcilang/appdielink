FROM node:18-alpine AS build

WORKDIR /app

COPY frontend-web/package.json frontend-web/package-lock.json ./
RUN npm ci

COPY frontend-web/ ./

ARG VITE_API_URL=/api/v1
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

FROM caddy:2-alpine

COPY docker/caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv

