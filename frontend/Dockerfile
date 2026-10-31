FROM node:24-alpine AS builder
ARG VITE_BASE_PATH=/
ENV VITE_BASE_PATH=${VITE_BASE_PATH}
WORKDIR /app
COPY package*.json ./
RUN npm ci --ignore-scripts
COPY . .
RUN npm run build

FROM nginxinc/nginx-unprivileged:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY nginx-securite.conf /etc/nginx/securite.conf
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 8080
