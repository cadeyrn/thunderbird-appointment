FROM nginx:stable

# Copy over files
COPY . /build/frontend

# Copy over the staging config
RUN mv /build/frontend/.env.staging.example /build/frontend/.env.staging

RUN apt-get update && apt-get install -y apache2-utils

# Add Node 16 support
RUN curl -fsSL https://deb.nodesource.com/setup_16.x | bash - &&\
apt-get install -y nodejs

# Build site
RUN cd /build/frontend && npm install
RUN cd /build/frontend && npm run build-stage

# Use our custom nginx config
RUN rm /etc/nginx/conf.d/default.conf
COPY docker/etc/nginx/conf.d/appointments.conf /etc/nginx/conf.d/default.conf

RUN htpasswd -c -b -B /etc/nginx/.htpasswd demo thunderbird-appointments-2023

RUN cp -r /build/frontend/dist/. /usr/share/nginx/html

EXPOSE 80