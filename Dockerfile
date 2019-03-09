FROM python:3.7

ENV LOG_DIR /var/log/stemerald
ENV STEMERALD_CONFIG_FILE /etc/stemerald/config.yml

ARG entrypointfile

WORKDIR /root

COPY setup.py stemerald/
COPY alembic.ini stemerald/
COPY wsgi.py stemerald/
COPY migration/*.py stemerald/migration/
COPY migration/*.mako stemerald/migration/
COPY migration/versions/*.py stemerald/migration/versions/
COPY stemerald/*.py stemerald/stemerald/
COPY stemerald/controllers/*.py stemerald/stemerald/controllers/
COPY stemerald/models/*.py stemerald/stemerald/models/
COPY stemerald/templates/*.mako stemerald/stemerald/templates/

RUN apt-get update -y && apt-get install -y apt-utils build-essential gettext-base wait-for-it \
    inetutils-ping net-tools lsof telnet && rm -rf /var/lib/apt/lists/*
COPY config.template.yml /etc/stemerald/config.template.yml

RUN pip install -e stemerald/ && mkdir -p $LOG_DIR

#CMD ["stemerald", "-c $STEMERALD_CONFIG_FILE", "worker", "cleanup"]

#VOLUME ["/var/log/"]
#EXPOSE 8080

COPY .docker/$entrypointfile /docker-entrypoint.sh
ENTRYPOINT [ "/docker-entrypoint.sh" ]
