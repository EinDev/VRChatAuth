FROM alpine/git:latest as libs

COPY libs/vrchatapi-python vrchatapi-python
COPY patches patches
RUN git apply --directory vrchatapi-python --ignore-space-change patches/*

FROM python:3.13-alpine as base

RUN pip install --upgrade pip

RUN adduser -D worker
USER worker
WORKDIR /home/worker

COPY --chown=worker:worker requirements.txt ./
RUN pip install --user -r requirements.txt

ENV PATH="/home/worker/.local/bin:${PATH}"

COPY --from=libs --chown=worker:worker /git/vrchatapi-python vrchatapi-python
RUN pip install --user -e vrchatapi-python

COPY idp idp

FROM base as celery_worker
HEALTHCHECK CMD celery -A idp.celery.make_celery_monitoring inspect ping || exit 1
CMD [ "celery", "-A", "idp.celery.make_celery_worker", "worker", "--loglevel", "INFO", "-E"]

FROM base as celery_beat
HEALTHCHECK CMD celery -A idp.celery.make_celery_monitoring inspect ping || exit 1
CMD [ "celery", "-A", "idp.celery.make_celery_worker", "beat", "--loglevel", "INFO", "-s", "/home/worker/data/celerybeat-schedule"]

FROM base as celery_monitoring
COPY --chown=worker:worker requirements-dev.txt .
RUN pip install --user -r requirements-dev.txt
RUN rm requirements-dev.txt
CMD [ "celery", "-A", "idp.celery.make_celery_monitoring", "flower", "--broker_api=redis://redis" ]

FROM base as app-dev
COPY --chown=worker:worker run_dev.py .
ENV FLASK_APP=idp
EXPOSE 5000
EXPOSE 5555
CMD [ "python", "run_dev.py"]

FROM base as app-prod
COPY --chown=worker:worker run_prod.py .
EXPOSE 8080
CMD [ "python", "run_prod.py" ]