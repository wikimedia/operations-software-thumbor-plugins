.PHONY: coverage test up down build bash

# Coverage
coverage:
	coverage run -m pytest || coverage report

# Tests
single-test:
# The default timeout is not enough while testing some asynchronous methods. So
# ASYNC_TEST_TIMEOUT environment variable was set to 60 seconds.
	@ASYNC_TEST_TIMEOUT=60 pytest tests/integration/test_djvu.py

tests:
	@ASYNC_TEST_TIMEOUT=60 pytest tests/

offline-tests:
	@ASYNC_TEST_TIMEOUT=60 pytest tests/ --ignore 'tests/integration/test_proxy_loader.py' --ignore 'tests/integration/test_huge_video.py' --ignore 'tests/integration/test_https_loader.py' --ignore 'tests/integration/test_vips_https_loader.py' --ignore 'tests/integration/test_3d.py'

# Docker
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

bash:
	docker-compose exec thumbor bash