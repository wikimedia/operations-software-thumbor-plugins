# Thumbor Plugins

The Wikimedia media thumbnailing infrastructure is based on [Thumbor](https://github.com/thumbor/thumbor).
More info about Thumbor Plugins - https://wikitech.wikimedia.org/wiki/Thumbor

## Quick setup for local development

1. Clone this repository
2. Install Docker - https://www.docker.com
3. In project folder create configuration file **thumbor.conf** with extensions or other options that you want to use, see example below:
```ini
COMMUNITY_EXTENSIONS = [
    'wikimedia_thumbor.handler.images',
    'wikimedia_thumbor.handler.core',
    'wikimedia_thumbor.handler.healthcheck',
]

FILE_LOADER_ROOT_PATH = '/srv/wikimedia_thumbor/tests/integration/originals'
LOADER = 'thumbor.loaders.file_loader'
```
More information about configuration options you could find here - https://thumbor.readthedocs.io/en/latest/configuration.html

## Run project and tests

1. Run project:
```bash
sudo make build
```
After starting the project you should be able to access the application on http://localhost:8800
Healthcheck of thumbor custom application on http://localhost:8800/healthcheck
2. Run offline tests(The project must be launched already):
```bash
sudo make bash
make offline-tests
```
3. Run code coverage(The project must be launched already):
```bash
sudo make bash
make coverage
```
