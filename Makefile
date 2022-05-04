.PHONY: coverage test up down build bash

# Coverage
coverage:
	coverage run -m pytest || coverage report

# Tests
single-test:
	@pytest tests/integration/test_djvu.py

tests:
	@pytest tests/

offline-tests:
	@pytest tests/ --ignore 'tests/integration/test_proxy_loader.py' --ignore 'tests/integration/test_huge_video.py' --ignore 'tests/integration/test_https_loader.py' --ignore 'tests/integration/test_vips_https_loader.py' --ignore 'tests/integration/test_3d.py'

# Docker
up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose up -d --build

bash:
	docker-compose exec thumbor bash