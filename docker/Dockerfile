FROM python:3.11-alpine
ENV PYTHONPATH=/home/app/project/python
ENV AWS_DEFAULT_REGION=us-east-1
ENV AWS_ACCESS_KEY_ID=yadda
ENV AWS_SECRET_ACCESS_KEY=yadda

RUN pip install pytest pytest-cov boto3 moto[ec2]
WORKDIR /home/app/project
