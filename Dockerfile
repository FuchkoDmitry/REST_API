FROM python:3.8.10-alpine3.14

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
WORKDIR /code
COPY ./requirements.txt /code/requirements.txt
RUN pip install --upgrade pip && apk add --no-cache --virtual .build-deps g++ gcc make  \
    libc-dev libffi-dev libevent-dev musl-dev openssl-dev \
    && pip3 install --no-cache-dir --upgrade -r requirements.txt \
    && apk del .build-deps g++ gcc make libc-dev libffi-dev libevent-dev musl-dev openssl-dev
COPY . /code
EXPOSE 8080
