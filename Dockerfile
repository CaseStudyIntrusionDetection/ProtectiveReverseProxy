FROM python:3.8

ENV PRP_VERSION=1.0.0a

# install packages for proxy
RUN apt-get update && apt-get install -y nginx supervisor \
	&& pip3.8 install flask flup captcha \
	&& mkdir /proxy/ && chown www-data:www-data /proxy/ \
	&& mkdir /protection/ && chown www-data:www-data /protection/ 

# install the protection system
COPY --chown=www-data:www-data ./protection/requirements.txt ./protection/setup.py ./protection/
RUN cd /protection/ && pip3.8 install -r requirements.txt && chown -R www-data:www-data /protection/

# copy code folders
COPY --chown=www-data:www-data ./proxy/ ./proxy/
COPY --chown=www-data:www-data ./protection/ ./protection/

# nginx settings and startup
COPY ./conf/supervisor.conf /etc/supervisor/supervisord.conf 
COPY ./conf/nginx.conf /etc/nginx/nginx.conf
COPY ./conf/proxy.conf /etc/nginx/sites-enabled/default

# dummy ssl cert
RUN openssl req -new -newkey rsa:4096 -keyout /etc/ssl/private/self_sslkey.pem -days 365 -nodes -x509 -subj "/CN=www.proctective-proxy.dummy"   -out /etc/ssl/certs/self_sslcert.pem 

# open port
EXPOSE 80/tcp
EXPOSE 443/tcp

# run nginx and python flask
ENTRYPOINT ["/usr/bin/supervisord", "-c", "/etc/supervisor/supervisord.conf"]