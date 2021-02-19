FROM python:3.8

# install packages for proxy
RUN apt-get update && apt-get install -y nginx supervisor \
	&& pip3.8 install flask flup \
	&& mkdir /proxy/ && chown www-data:www-data /proxy/ \
	&& mkdir /protection/ && chown www-data:www-data /protection/ 

# code folders
COPY --chown=www-data:www-data ./proxy/*.py ./proxy/
COPY --chown=www-data:www-data ./protection/ ./protection/

# nginx settings and startup
COPY ./proxy/supervisor.conf /etc/supervisor/conf.d/supervisord.conf 
COPY ./proxy/nginx.conf /etc/nginx
COPY ./proxy/proxy.conf /etc/nginx/sites-enabled/default

# dummy ssl cert
RUN openssl req -new -newkey rsa:4096 -keyout /etc/ssl/private/self_sslkey.pem -days 365 -nodes -x509 -subj "/CN=www.proctective-proxy.dummy"   -out /etc/ssl/certs/self_sslcert.pem 

# open port
EXPOSE 80/tcp
EXPOSE 443/tcp

# run nginx and python flask
ENTRYPOINT ["/usr/bin/supervisord"]