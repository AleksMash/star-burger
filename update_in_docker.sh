#!/bin/bash

set -e

source .env

git  pull

docker-compose -f docker-compose.prod.yml up --build -d

if [[ -n $RB_TOKEN ]]; then
  rb_token=$(echo $RB_TOKEN | tr -d '\r')
  rev=$(git rev-parse --short HEAD)
  curl    -H "X-Rollbar-Access-Token: $rb_token" \
          -H "Content-Type: application/json" \
          -X  POST \
          -d  '{"environment": "production", "revision":"'${rev}'", "rollbar_name": "Alex", "local_username": "Alex", "comment": "deployment in docker", "status": "succeeded"}'\
          https://api.rollbar.com/api/1/deploy
  echo "Отметка о деплое направлена в Rollbar"
  else
    echo "Токен Rollbar не задан. Отметка о деплое не будет направлена"
fi

echo "Приложение обновлено в Docker"