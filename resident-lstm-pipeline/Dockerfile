FROM python:3.6.9

RUN apt update

COPY requirements.txt   .
RUN pip install -r requirements.txt

RUN apt install vim -y

COPY liao_newchebyLSTM.py   .
COPY test.csv   .
COPY model.h5   .

CMD ["/bin/bash", "-c", "tail -f /dev/null"]

