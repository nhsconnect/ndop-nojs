FROM python:3.6

COPY ndop-mock/requirements.txt requirements.txt

RUN pip install --upgrade pip && pip install -r requirements.txt

WORKDIR "app"

CMD flask run
