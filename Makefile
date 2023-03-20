.PHONY: code-coverage docker_code-coverage test offline-test online-test lint up down build bash docker_test docker_offline-test docker_online-test 3d2png install

# Settings
# The default timeout is not enough while testing some asynchronous methods. So
# we use this to increase the timeout by setting the ASYNC_TEST_TIMEOUT
# environment variable below.
ENV_ASYNC_TEST_TIMEOUT = 60

# Code coverage
code-coverage:
	ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) coverage run --source=wikimedia_thumbor/ -m pytest || coverage html -d coverage

docker_code-coverage:
	docker build -t thumbor-code-coverage --target code-coverage -f .pipeline/blubber.yaml .
	mkdir -m a+w coverage
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) -it --mount type=bind,source=`pwd`/coverage,dst=/srv/service/coverage thumbor-code-coverage

# Tests
test: lint
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/

docker_test:
	docker build -t thumbor-test --target test -f .pipeline/blubber.yaml .
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-test

offline-test:
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/ --ignore 'tests/integration/test_proxy_loader.py' --ignore 'tests/integration/test_huge_video.py' --ignore 'tests/integration/test_https_loader.py' --ignore 'tests/integration/test_vips_https_loader.py'

# Unlike the online tests, the Docker container for this group of tests can
# be run without an internet connection since all necessary data is local.
docker_offline-test:
	docker build -t thumbor-offline-test --target offline-test -f .pipeline/blubber.yaml .
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-offline-test

online-test:
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/integration/test_proxy_loader.py tests/integration/test_huge_video.py tests/integration/test_https_loader.py tests/integration/test_vips_https_loader.py

# This group of tests requires an internet connection because there are test
# cases that make HTTP requests to third-party services.
docker_online-test:
	docker build -t thumbor-online-test --target online-test -f .pipeline/blubber.yaml .
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-online-test

# Linter
lint:
	flake8 ./tests ./wikimedia_thumbor

# Docker
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

bash:
	docker-compose exec thumbor bash

3d2png:
	git clone https://github.com/wikimedia/3d2png.git
	npm install 3d2png
	ln -s /srv/service/node_modules/.bin/3d2png /opt/lib/python/site-packages/bin/
