.PHONY: code-coverage docker_code-coverage test offline-test online-test lint up down build bash docker_test docker_offline-test docker_online-test 3d2png needs-docker install

# Settings
# The default timeout is not enough while testing some asynchronous methods. So
# we use this to increase the timeout by setting the ASYNC_TEST_TIMEOUT
# environment variable below.
ENV_ASYNC_TEST_TIMEOUT = 60

# Prevent some targets from being run on the host, to avoid confusion.
# The IN_DOCKER env var is set in .pipeline/blubber.yaml
needs-docker:
	@if [ -z "$(IN_DOCKER)" ]; then \
		echo "Error: This target must be run via Docker (IN_DOCKER not set)"; \
		exit 1; \
	fi

# Code coverage
code-coverage: needs-docker
	ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) coverage run --source=wikimedia_thumbor/ -m pytest || coverage html -d coverage

build-test:
	docker build -t thumbor-test --target test -f .pipeline/blubber.yaml .

docker_code-coverage: build-test
	mkdir -m a+w coverage
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) -it --mount type=bind,source=`pwd`/coverage,dst=/srv/service/coverage thumbor-test code-coverage

# Tests
test: needs-docker lint
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/

docker_test: build-test
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-test test

offline-test: needs-docker
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/ --ignore 'tests/integration/test_proxy_loader.py' --ignore 'tests/integration/test_huge_video.py' --ignore 'tests/integration/test_https_loader.py' --ignore 'tests/integration/test_vips_https_loader.py'

# Unlike the online tests, the Docker container for this group of tests can
# be run without an internet connection since all necessary data is local.
docker_offline-test: build-test
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-test offline-test

online-test: needs-docker
	@ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) pytest tests/integration/test_proxy_loader.py tests/integration/test_huge_video.py tests/integration/test_https_loader.py tests/integration/test_vips_https_loader.py

# This group of tests requires an internet connection because there are test
# cases that make HTTP requests to third-party services.
docker_online-test: build-test
	docker run --env ASYNC_TEST_TIMEOUT=$(ENV_ASYNC_TEST_TIMEOUT) thumbor-test online-test

# Linter
lint: needs-docker
	flake8 ./tests ./wikimedia_thumbor

# Docker
up:
	docker compose up -d

down:
	docker compose down

build:
	docker compose up -d --build

bash:
	docker compose exec thumbor bash

3d2png: needs-docker
	git clone https://github.com/wikimedia/3d2png.git
	cd 3d2png; npm install
	ln -s /srv/service/3d2png/3d2png.js /opt/lib/venv/bin/3d2png
