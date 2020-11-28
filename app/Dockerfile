FROM python:3.8.3-alpine


WORKDIR /usr/src/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update \
    && apk add postgresql-dev gcc python3-dev musl-dev

RUN apk add zlib-dev jpeg-dev gcc musl-dev

RUN pip install --upgrade pip
COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./scripts/entrypoint.sh .
COPY . .

COPY ./core/token.pkl .
COPY . .

ENTRYPOINT ["/usr/src/app/scripts/entrypoint.sh"]
