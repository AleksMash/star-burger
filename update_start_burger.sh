#!/bin/bash

set -e

source .env

cd /opt/star-burger

git  pull

/opt/star-burger/venv/bin/pip install -r  requirements.txt

npm ci --dev

./node_modules/.bin/parcel build bundles-src/index.js --dist-dir bundles --public-url="./"

/opt/star-burger/venv/bin/python3 /opt/star-burger/manage.py migrate --noinput

/opt/star-burger/venv/bin/python3 /opt/star-burger/manage.py collectstatic --noinput

systemctl restart star-burger2

if [[ -n $RB_TOKEN ]]; then
  rb_token=$(echo $RB_TOKEN | tr -d '\r')
  rev=$(git rev-parse --short HEAD)
  curl    -H "X-Rollbar-Access-Token: $rb_token" \
          -H "Content-Type: application/json" \
          -X  POST \
          -d  '{"environment": "production", "revision":"'${rev}'", "rollbar_name": "Alex", "local_username": "Alex", "comment": "deployment", "status": "succeeded"}'\
          https://api.rollbar.com/api/1/deploy
  echo "Отметка о деплое направлена в Rollbar"
  else
    echo "Токен Rollbar не задан. Отметка о деплое не будет направлена"
fi

echo "Код обновлен, юнит 'star-burger2.service' перезапущен"
