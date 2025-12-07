PYTHON ?= python
DJANGO_SETTINGS_MODULE ?= smarthr360_backend.config.local
export DJANGO_SETTINGS_MODULE

.PHONY: install lint type test coverage makemigrations-check migrate migrate-check collectstatic runserver shell dev-up dev-down prod-up prod-down prod-logs

install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

lint:
	$(PYTHON) -m ruff check .

type:
	$(PYTHON) -m mypy --ignore-missing-imports .

test:
	$(PYTHON) manage.py test

coverage:
	$(PYTHON) -m coverage run --parallel-mode manage.py test
	$(PYTHON) -m coverage combine
	$(PYTHON) -m coverage report -m

makemigrations-check:
	$(PYTHON) manage.py makemigrations --check --dry-run

migrate:
	$(PYTHON) manage.py migrate --noinput

migrate-check:
	$(PYTHON) manage.py migrate --check

collectstatic:
	$(PYTHON) manage.py collectstatic --noinput

runserver:
	$(PYTHON) manage.py runserver 0.0.0.0:8000

shell:
	$(PYTHON) manage.py shell

dev-up:
	docker compose --profile dev up --build

dev-down:
	docker compose --profile dev down

prod-up:
	docker compose --profile prod up --build -d

prod-down:
	docker compose --profile prod down

prod-logs:
	docker compose --profile prod logs -f
