.PHONY: code-coverage docker_code-coverage single-test test offline-test online-test up down build bash docker_test 3d2png install

# Code coverage
code-coverage:
	coverage run --source=wikimedia_thumbor/ -m pytest || coverage html -d coverage

docker_code-coverage:
	docker build -t thumbor-code-coverage --target code-coverage -f .pipeline/blubber.yaml .
	mkdir -m a+w coverage
	docker run -it --mount type=bind,source=`pwd`/coverage,dst=/srv/service/coverage thumbor-code-coverage

# Tests
single-test:
# The default timeout is not enough while testing some asynchronous methods. So
# ASYNC_TEST_TIMEOUT environment variable was set to 60 seconds.
	@ASYNC_TEST_TIMEOUT=60 pytest tests/integration/test_djvu.py

test:
	@ASYNC_TEST_TIMEOUT=60 pytest tests/

offline-test:
	@ASYNC_TEST_TIMEOUT=60 pytest tests/ --ignore 'tests/integration/test_proxy_loader.py' --ignore 'tests/integration/test_huge_video.py' --ignore 'tests/integration/test_https_loader.py' --ignore 'tests/integration/test_vips_https_loader.py' --ignore 'tests/integration/test_3d.py'

online-test:
	@ASYNC_TEST_TIMEOUT=60 pytest tests/integration/test_proxy_loader.py tests/integration/test_huge_video.py tests/integration/test_https_loader.py tests/integration/test_vips_https_loader.py tests/integration/test_3d.py

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

docker_test:
	docker build -t thumbor-test --target test -f .pipeline/blubber.yaml .
	docker run thumbor-test

install: 3d2png
	python setup.py install
