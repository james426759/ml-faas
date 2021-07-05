FROM --platform=${TARGETPLATFORM:-linux/amd64} ghcr.io/openfaas/classic-watchdog:0.1.5 as watchdog
FROM --platform=${TARGETPLATFORM:-linux/amd64} python:3.7

ARG TARGETPLATFORM
ARG BUILDPLATFORM

# Allows you to add additional packages via build-arg
ARG ADDITIONAL_PACKAGE

COPY --from=watchdog /fwatchdog /usr/bin/fwatchdog
RUN chmod +x /usr/bin/fwatchdog
RUN apt update

WORKDIR /home/app/

# User define package
# RUN pip install pandas

COPY index.py           .
COPY requirements.txt   .

RUN mkdir -p /home/app/python && chmod -R 777 /home/app

ENV PATH=$PATH:/home/app/.local/bin:/home/app/python/bin/
ENV PYTHONPATH=$PYTHONPATH:/home/app/python

RUN pip install -r requirements.txt --target=/home/app/python

RUN mkdir -p function
RUN touch ./function/__init__.py

WORKDIR /home/app/function/
COPY function/requirements.txt	.

RUN pip install -r requirements.txt --target=/home/app/python

WORKDIR /home/app/

USER root

COPY function           function

RUN chmod -R 777 /home/app/python

ENV fprocess="python3 index.py"
EXPOSE 8080

HEALTHCHECK --interval=3s CMD [ -e /tmp/.lock ] || exit 1

CMD ["fwatchdog"]
