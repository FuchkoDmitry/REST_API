#! /bin/sh

sleep 10
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic

if [ "$DJANGO_SUPERUSER_USERNAME" ]
then
  python manage.py createsuperuser \
    --no-input \
    --email $DJANGO_SUPERUSER_EMAIL
fi

gunicorn orders.wsgi:application --bind 0.0.0.0:8080
exec "$@"
