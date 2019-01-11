FROM python:3.7

ENV LOG_DIR /var/log/stemerald

COPY ../../alembic.ini ../../wsgi.py ../../migration ../../stemerald/*.py ../../stemerald/controllers ../../stemerald/models ../../stemerald/models/templates ./

COPY ../config.yml /etc/stemerald/
RUN sudo apt-get update -y && sudo apt-get install -y apt-utils build-essential

RUN pip install . && mkdir -p $LOG_DIR

CMD ["stemerald", "admin", "create-db", "--base-data"]

VOLUME ["/var/log/"]