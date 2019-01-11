FROM python:3.7

ENV LOG_DIR /var/log/stemerald
ENV STEMERALD_CONFIG_FILE /etc/stemerald/config.yml

COPY ../../alembic.ini ../../wsgi.py ../../migration ../../stemerald/*.py ../../stemerald/controllers ../../stemerald/models ../../stemerald/models/templates ./

COPY ../config.yml /etc/stemerald/
RUN sudo apt-get update -y && sudo apt-get install -y apt-utils build-essential

RUN pip install . && mkdir -p $LOG_DIR

CMD ["stemerald", "-c $STEMERALD_CONFIG_FILE", "admin", "create-db", "--base-data"]
CMD ["stemerald", "-c $STEMERALD_CONFIG_FILE", "migrate", "upgrade", "head"]

VOLUME ["/var/log/"]

COPY entrypoint.sh /docker-entrypoint.sh
ENTRYPOINT [ "/docker-entrypoint.sh" ]
