# Thumbor Plugins

The Wikimedia media thumbnailing infrastructure is based on [Thumbor](https://github.com/thumbor/thumbor).
More info about Thumbor Plugins - https://wikitech.wikimedia.org/wiki/Thumbor

## Quick setup for local development

1. Clone this repository
2. Install Docker - https://www.docker.com
3. In the project folder create configuration file **thumbor.conf** with extensions or other options that you want to use, see example below:
```ini
FILE_LOADER_ROOT_PATH = '/srv/service/tests/integration/originals'

STORAGE = 'thumbor.storages.no_storage'
LOADER = 'wikimedia_thumbor.loader.file'

LOADER_EXCERPT_LENGTH = 4096
HTTP_LOADER_REQUEST_TIMEOUT = 60
HTTP_LOADER_TEMP_FILE_TIMEOUT = 20

ENGINE = 'wikimedia_thumbor.engine.proxy'
RESPECT_ORIENTATION = True

FFMPEG_PATH = '/usr/bin/ffmpeg'
EXIFTOOL_PATH = '/usr/bin/exiftool'
VIPS_PATH = '/usr/bin/vips'
FFPROBE_PATH = '/usr/bin/ffprobe'
XCF2PNG_PATH = '/usr/bin/xcf2png'
GHOSTSCRIPT_PATH = '/usr/bin/gs'
DDJVU_PATH = '/usr/bin/ddjvu'
RSVG_CONVERT_PATH = '/usr/bin/rsvg-convert'
THREED2PNG_PATH = '/opt/lib/python/site-packages/bin/3d2png'
XVFB_RUN_PATH = '/usr/bin/xvfb-run'
CONVERT_PATH = '/usr/bin/convert'
CWEBP_PATH = '/usr/bin/cwebp'
SUBPROCESS_TIMEOUT_PATH = '/usr/bin/timeout'

SUBPROCESS_USE_TIMEOUT = True
SUBPROCESS_TIMEOUT = 60

CHROMA_SUBSAMPLING = '4:2:0'
QUALITY = 79
QUALITY_LOW = 40
DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'
MAX_ANIMATED_GIF_AREA = 500 * 200 * 60

COMMUNITY_EXTENSIONS = [
    'wikimedia_thumbor.handler.images',
    'wikimedia_thumbor.handler.core',
    'wikimedia_thumbor.handler.healthcheck'
]

EXIF_FIELDS_TO_KEEP = ['Artist', 'Copyright', 'ImageDescription']
EXIF_TINYRGB_PATH = '/srv/service/tinyrgb.icc'
EXIF_TINYRGB_ICC_REPLACE = 'sRGB IEC61966-2.1'

VIPS_ENGINE_MIN_PIXELS = 20000000

PROXY_ENGINE_ENGINES = [
    ('wikimedia_thumbor.engine.xcf', ['xcf']),
    ('wikimedia_thumbor.engine.djvu', ['djvu']),
    ('wikimedia_thumbor.engine.vips', ['tiff', 'png']),
    ('wikimedia_thumbor.engine.tiff', ['tiff']),
    ('wikimedia_thumbor.engine.ghostscript', ['pdf']),
    ('wikimedia_thumbor.engine.gif', ['gif']),
    ('wikimedia_thumbor.engine.stl', ['stl']),
    ('wikimedia_thumbor.engine.svg', ['svg']),
    ('wikimedia_thumbor.engine.imagemagick', ['jpg', 'png', 'webp']),
]

FILTERS = [
    'wikimedia_thumbor.filter.conditional_sharpen',
    'wikimedia_thumbor.filter.format',
    'wikimedia_thumbor.filter.lang',
    'wikimedia_thumbor.filter.page',
    'wikimedia_thumbor.filter.crop',
    'wikimedia_thumbor.filter.flip',
    'thumbor.filters.quality',
    'thumbor.filters.rotate'
]
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
