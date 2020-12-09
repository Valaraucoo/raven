#!/bin/sh

NOCOLOR='\033[0m'
GREEN='\033[0;32m'

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      echo "Waiting for PostgreSQL"
      sleep 0.1
    done

    echo "${GREEN}PostgreSQL started${NOCOLOR}"
fi

#python manage.py flush --no-input

echo "${GREEN}Running django server...${NOCOLOR}"
python manage.py migrate

exec "$@"
