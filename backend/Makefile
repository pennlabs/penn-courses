# Commands
runserver:
	PIPENV_VERBOSITY=-1
	pipenv run python manage.py runserver 0.0.0.0:8000

# Run tests
runtests:
	PIPENV_VERBOSITY=-1
	pipenv run python manage.py test


# Launch docker database & cache
launchdb:
	docker compose up -d

# Make migrations (when models are changed)
makemigrations:
	python manage.py makemigrations

# Migrate (when migrations are created)
migrate:
	python manage.py migrate

# Lint
lint:
	PIPENV_VERBOSITY=-1
	pipenv run black -l100 .
	pipenv run isort .
	pipenv run flake8 .

# Load data from file
load:
	PGPASSWORD=postgres
	psql template1 -c 'drop database postgres;' -h localhost -U penn-courses
	psql template1 -c 'create database postgres with owner "penn-courses";' -h localhost -U penn-courses
	psql -h localhost -d postgres -U penn-courses -f ./pcx_test.sql


## Install dependencies
UNAME := $(shell uname)
ifeq ($(UNAME), Linux)
install:
	apt-get install gcc python3-dev libpq-dev;apt-get install gdal-bin libgdal-dev python3-gdal binutils libproj-dev
	pipenv install --dev
endif
ifeq ($(UNAME), Darwin)
install:
	LDFLAGS="-L$(shell brew --prefix openssl)/lib"
	CPPFLAGS="-I$(shell brew --prefix openssl)/include"
	brew install postgresql;brew install openssl;brew unlink openssl && brew link openssl --force;brew install gdal; brew install libgeoip
	pipenv install --dev
endif