# entregasdalu — compose "caddy" service. Build context: repo ROOT (to reach frontend/).
# Multi-stage: a node builder runs `vite build`, then the SPA is baked into the
# official caddy image → one-command deploy, no Node on the server, no stale-build
# drift (design.md §7.3). The generated API types are committed, so the build needs
# no running backend.
FROM node:22-slim AS build
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM caddy:2-alpine
COPY caddy/Caddyfile /etc/caddy/Caddyfile
COPY --from=build /app/dist /srv/www
