FROM python:3.6.9

RUN apt update

COPY requirements.txt   .
RUN pip install -r requirements.txt

COPY liao_newcheby_random.py   .
COPY test.csv   .

CMD ["/bin/bash", "-c", "tail -f /dev/null"]

