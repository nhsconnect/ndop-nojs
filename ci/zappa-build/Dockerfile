FROM python:3.6

COPY requirements.txt requirements.txt

SHELL ["/bin/bash", "-c"]

RUN pip install virtualenv && \
    virtualenv /var/venv && \
    source /var/venv/bin/activate && \
    pip install -r requirements.txt && \
    deactivate

WORKDIR "/var/task"

CMD ["zappa"]
