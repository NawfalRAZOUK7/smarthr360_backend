web: gunicorn smarthr360_backend.wsgi:application --bind 0.0.0.0:$PORT --workers 4 --threads 2 --timeout 120 --access-logfile - --error-logfile -
release: python manage.py migrate --no-input
