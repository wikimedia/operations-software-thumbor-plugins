.PHONY: coverage test up down build bash

coverage:
	@nosetests -sv --with-coverage --cover-package=wikimedia_thumbor

test:
	@nosetests -sv

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

bash:
	docker-compose exec thumbor bash