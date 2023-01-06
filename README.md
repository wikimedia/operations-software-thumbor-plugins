# Thumbor Plugins

The Wikimedia media thumbnailing infrastructure is based on [Thumbor](https://github.com/thumbor/thumbor).
More info about Thumbor Plugins - https://wikitech.wikimedia.org/wiki/Thumbor

## Quick setup for local development

1. Clone this repository
2. Install Docker - https://www.docker.com
3. In the project folder create configuration file **thumbor.conf** with extensions or other options that you want to use, see example below:
```ini
COMMUNITY_EXTENSIONS = [
    'wikimedia_thumbor.handler.images',
    'wikimedia_thumbor.handler.core',
    'wikimedia_thumbor.handler.healthcheck',
]

FILE_LOADER_ROOT_PATH = '/srv/service/tests/integration/originals'
LOADER = 'thumbor.loaders.file_loader'
```
More information about configuration options you could find in the Thumbor docs - https://thumbor.readthedocs.io/en/latest/configuration.html
Also, you can use the current Thumbor Plugins configurations that are used in the production, this can help to set up pretty much the same environment as in the production version - https://gerrit.wikimedia.org/r/plugins/gitiles/operations/deployment-charts/+/refs/heads/master/charts/thumbor/templates/_thumbor_server.tpl

## Run project and tests

1. Build and run project:
```bash
make build
```
After starting the project you should be able to access the application at http://localhost:8800
Healthcheck of Thumbor custom application at http://localhost:8800/healthcheck
To understand how to make requests to the local Thumbor server, it will be useful to learn how tests work. For instance, here is the link which returns a cropped image - http://localhost:8800/thumbor/unsafe/450x/Carrie.jpg For this case, the minimal Thumbor configurations that are mentioned above will be enough.
2. Run both flake8 linter and all tests:
It requires an internet connection because there are test cases that make HTTP requests to third-party services.
```bash
make docker_test
```
3. Run code coverage:
```bash
make docker_code-coverage
```
When the thumbor-code-coverage container will finish its work, you can see the HTML code coverage report by opening the following file *coverage/index.html* in a browser.
