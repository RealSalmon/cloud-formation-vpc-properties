FROM python:alpine3.6

COPY requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# requirements for running tests
RUN apk add --update-cache gcc musl-dev libffi-dev openssl-dev && \
    pip install pytest pytest-cov moto
