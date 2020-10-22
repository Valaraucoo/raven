#!/bin/sh

NOCOLOR='\033[0m'
GREEN='\033[0;32m'

echo "${GREEN}Running Tests${NOCOLOR}"
docker-compose exec web coverage run --source='.' --omit=*/venv/*,*/migrations/*,*/__init__* manage.py test
docker-compose exec web coverage report

echo "${GREEN}Running flake8${NOCOLOR}"
docker-compose exec web flake8 .

echo "${GREEN}Running isort${NOCOLOR}"
docker-compose exec web isort .

echo "${GREEN}Done.${NOCOLOR}"