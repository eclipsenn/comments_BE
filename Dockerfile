FROM python:3.6-slim

RUN groupadd dmishin && useradd --create-home --home-dir /home/dmishin -g dmishin dmishin
RUN apt-get update && apt-get install -y wget

# dockerize allows services to wait for each other
# https://docs.docker.com/compose/startup-order/
ENV DOCKERIZE_VERSION v0.5.0
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && rm dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz

COPY . /opt/comments/
RUN pip install -r /opt/comments/requirements.txt
WORKDIR /opt/comments
RUN chown -R dmishin /opt/comments
USER dmishin
