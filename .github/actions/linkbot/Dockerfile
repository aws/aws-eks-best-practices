FROM python:3.11

COPY requirements.txt /

RUN pip install -r /requirements.txt

COPY linkbot /opt/linkbot

ENV PYTHONPATH "${PYTHONPATH}:/opt"
ENV PYTHONUNBUFFERED "1"

CMD python -m linkbot