# check=skip=InvalidDefaultArgInFrom
ARG NODE_VERSION
ARG NGINX_VERSION

FROM node:${NODE_VERSION} AS builder

WORKDIR /app

COPY package.json *package-lock.json* ./

RUN --mount=type=cache,target=/root/.npm npm ci

COPY . .

RUN npm run build 

FROM nginxinc/nginx-unprivileged:${NGINX_VERSION} AS runner

USER root

COPY nginx.conf /etc/nginx/nginx.conf

COPY --chown=nginx:nginx --from=builder /app/dist/*/browser /usr/share/nginx/html

# Copiar el script de entrada antes de cambiar al usuario nginx
COPY entrypoint.sh /entrypoint.sh

USER nginx

EXPOSE 8080

# El script procesa el JSON y luego delega el control a Nginx
ENTRYPOINT ["/entrypoint.sh", "nginx", "-c", "/etc/nginx/nginx.conf"]
CMD ["-g", "daemon off;"]