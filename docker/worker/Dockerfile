FROM python:3.7

ENV LOG_DIR /var/log/stemerald
ENV STEMERALD_CONFIG_FILE /etc/stemerald/config.yml

WORKDIR /root

COPY setup.py stemerald/
COPY alembic.ini stemerald/
COPY wsgi.py stemerald/
COPY migration/*.py stemerald/migration/
COPY migration/*.mako stemerald/migration/
COPY stemerald/*.py stemerald/stemerald/
COPY stemerald/controllers/*.py stemerald/stemerald/controllers/
COPY stemerald/models/*.py stemerald/stemerald/models/
COPY stemerald/templates/*.mako stemerald/stemerald/templates/

RUN apt-get update -y && apt-get install -y apt-utils build-essential gettext-base
COPY docker/config.yml /etc/stemerald/config.template

RUN pip install -e stemerald/ && mkdir -p $LOG_DIR

CMD ["envsubst < /etc/stemerald/config.template > $STEMERALD_CONFIG_FILE"]
CMD ["stemerald", "-c $STEMERALD_CONFIG_FILE", "worker", "cleanup"]

VOLUME ["/var/log/"]

COPY docker/server/entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT [ "/docker-entrypoint.sh" ]
