FROM nginx:alpine
RUN rm -f /etc/nginx/conf.d/default.conf
COPY modeles /etc/nginx/modeles
COPY 40-choisir-config.sh /docker-entrypoint.d/40-choisir-config.sh
