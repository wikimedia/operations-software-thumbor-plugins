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
3. Run code coverage:
```bash
sudo make docker_code-coverage
```
When the thumbor-code-coverage container will finish its work, you can see the HTML code coverage report
by opening the following file *coverage/index.html* in a browser.

## Debug tests

There is a simple way to debug tests using the PyCharm IDE debugger.
### PyCharm version
2022.2 (Professional Edition)
1. The Docker container of the thumbor-plugins should be already built.
2. Follow the official instruction about
[configuring an interpreter using Docker](https://www.jetbrains.com/help/pycharm/2022.2/using-docker-as-a-remote-interpreter.html)
till the Preparing an example chapter.
3. Change the Python interpreter using
[the Python Interpreter selector](https://www.jetbrains.com/help/pycharm/2022.2/configuring-python-interpreter.html#add-existing-interpreter).
4. In the new pop-up that opens, go to the Interpreter Settings.
5. Expand the list of the available interpreters and click the Show All link.
6. Click the plus button.
7. Click the Docker in a new window that opens.
8. Specify the server, the image name and the python interpreter path in the Docker tab. By default, the server is
`Docker`, the image name is `thumbor-plugins_thumbor:latest` and the Python interpreter is `python3`.
9. Start debugging. Learn how to use the PyCharm debugger following
[this official tutorial](https://www.jetbrains.com/help/pycharm/2022.2/part-1-debugging-python-code.html).
10. Please, take into consideration:
    * There are tests which require setting the environment variable `ASYNC_TEST_TIMEOUT=60`. If a test fails with
    `TimeoutError`, it means that the variable should be set in the test configurations section.
    * It seems that PyCharm has a bug related to not detecting breakpoints before `breakpoint()` has been placed
    somewhere in a test. But the bug may not happen with all the tests. For more information, read this issue on
    [intellij-support.jetbrains.com](https://intellij-support.jetbrains.com/hc/en-us/community/posts/360008107400-PyCharm-2020-1-not-stopping-on-breakpoints-anymore-).