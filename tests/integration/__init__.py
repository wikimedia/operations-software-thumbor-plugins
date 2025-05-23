import platform
import os.path
from tempfile import NamedTemporaryFile

from PIL import Image

from ssim import compute_ssim

from tornado.testing import AsyncHTTPTestCase, get_async_test_timeout
from tornado.httpclient import HTTPRequest

from thumbor.config import Config
from thumbor.context import Context, ServerParameters
from thumbor.importer import Importer
from thumbor.utils import logger
from shutil import which

from wikimedia_thumbor.app import App


# AsyncHTTPTestCase doesn't set request_timeout
HTTPRequest._DEFAULTS['request_timeout'] = get_async_test_timeout()


class WikimediaTestCase(AsyncHTTPTestCase):
    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.STORAGE = 'thumbor.storages.no_storage'
        cfg.LOADER = 'wikimedia_thumbor.loader.file'

        cfg.LOADER_EXCERPT_LENGTH = 4096
        cfg.HTTP_LOADER_REQUEST_TIMEOUT = 60
        cfg.HTTP_LOADER_TEMP_FILE_TIMEOUT = 20

        cfg.FILE_LOADER_ROOT_PATH = os.path.join(
            os.path.dirname(__file__),
            'originals'
        )
        cfg.ENGINE = 'wikimedia_thumbor.engine.proxy'
        cfg.RESPECT_ORIENTATION = True

        cfg.FFMPEG_PATH = which('ffmpeg')
        cfg.EXIFTOOL_PATH = which('exiftool')
        cfg.VIPS_PATH = which('vips')
        cfg.FFPROBE_PATH = which('ffprobe')
        cfg.GHOSTSCRIPT_PATH = which('gs')
        cfg.DDJVU_PATH = which('ddjvu')
        cfg.RSVG_CONVERT_PATH = which('rsvg-convert')
        cfg.THREED2PNG_PATH = which('3d2png')
        cfg.XVFB_RUN_PATH = which('xvfb-run')
        cfg.CONVERT_PATH = which('convert')
        cfg.CWEBP_PATH = which('cwebp')
        timeout = which(
            'gtimeout' if platform.system() == 'Darwin' else 'timeout'
        )
        cfg.SUBPROCESS_TIMEOUT_PATH = timeout

        cfg.SUBPROCESS_USE_TIMEOUT = True
        cfg.SUBPROCESS_TIMEOUT = 60

        cfg.CHROMA_SUBSAMPLING = '4:2:0'
        cfg.QUALITY = 79
        cfg.QUALITY_LOW = 40
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'
        cfg.MAX_ANIMATED_GIF_AREA = 500 * 200 * 60
        cfg.GHOSTSCRIPT_ENGINE_DEFAULT_DPI = 150

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.images',
            'wikimedia_thumbor.handler.core'
        ]

        cfg.EXIF_FIELDS_TO_KEEP = ['Artist', 'Copyright', 'ImageDescription']
        cfg.EXIF_TINYRGB_PATH = os.path.realpath(
            os.path.join(os.path.dirname(__file__), '..', '..', 'tinyrgb.icc')
        )
        cfg.EXIF_TINYRGB_ICC_REPLACE = 'sRGB IEC61966-2.1'

        cfg.VIPS_ENGINE_MIN_PIXELS = 20000000

        cfg.PROXY_ENGINE_ENGINES = [
            ('wikimedia_thumbor.engine.djvu', ['djvu']),
            ('wikimedia_thumbor.engine.vips', ['tiff', 'png']),
            ('wikimedia_thumbor.engine.tiff', ['tiff']),
            ('wikimedia_thumbor.engine.ghostscript', ['pdf']),
            ('wikimedia_thumbor.engine.gif', ['gif']),
            ('wikimedia_thumbor.engine.stl', ['stl']),
            # SVG should alwayd be the one before last, because of how broad it is (trying all XML documents)
            ('wikimedia_thumbor.engine.svg', ['svg']),
            # Imagemagick should always be last, to act as a catch-all since Thumbor defaults to assuming JPG when the document is unknown
            ('wikimedia_thumbor.engine.imagemagick', ['jpg', 'png', 'webp', 'xcf']),
        ]

        cfg.FILTERS = [
            'wikimedia_thumbor.filter.conditional_sharpen',
            'wikimedia_thumbor.filter.format',
            'wikimedia_thumbor.filter.lang',
            'wikimedia_thumbor.filter.page',
            'wikimedia_thumbor.filter.crop',
            'wikimedia_thumbor.filter.flip',
            'thumbor.filters.quality',
            'thumbor.filters.rotate'
        ]

        return cfg

    def get_app(self):
        server_params = ServerParameters(None, None, None, None, None, None)

        cfg = self.get_config()

        importer = Importer(cfg)
        importer.import_modules()
        self.ctx = Context(server_params, cfg, importer)
        application = App(self.ctx)

        return application

    def run_and_check_ssim_and_size(
        self,
        url,
        mediawiki_reference_thumbnail,
        perfect_reference_thumbnail,
        expected_width,
        expected_height,
        expected_ssim,
        size_tolerance,
        headers={}
    ):
        """Request URL and check ssim and size.

        Arguments:
        url -- thumbnail URL
        mediawiki_reference_thumbnail -- reference thumbnail file
        perfect_reference_thumbnail -- perfect lossless version of the target thumbnail, for visual comparison
        expected_width -- expected thumbnail width
        expected_height -- expected thumbnail height
        expected_ssim -- minimum SSIM score
        size_tolerance -- maximum file size ratio between reference and result
        headers -- headers to be passed alongside the HTTP get
        """
        try:
            result = self.fetch(url, headers=headers)
        except Exception as e:
            assert False, 'Exception occured: %r' % e

        assert result is not None, 'No result'
        assert result.code == 200, 'Response code: %s' % result.code

        result.buffer.seek(0)

        generated = Image.open(result.buffer)

        expected_path = os.path.join(
            os.path.dirname(__file__),
            'thumbnails',
            mediawiki_reference_thumbnail
        )

        visual_expected_path = os.path.join(
            os.path.dirname(__file__),
            'thumbnails',
            perfect_reference_thumbnail
        )
        visual_expected = Image.open(visual_expected_path).convert(generated.mode)

        assert generated.size[0] == expected_width, \
            'Width differs: %d (should be == %d)\n' % (generated.size[0], expected_width)

        assert generated.size[1] == expected_height, \
            'Height differs: %d (should be == %d)\n' % (generated.size[1], expected_height)

        ssim = compute_ssim(generated, visual_expected)

        try:
            assert ssim >= expected_ssim, 'Images too dissimilar: %f (should be >= %f)\n' % (ssim, expected_ssim)
        except AssertionError as e:
            output_file = NamedTemporaryFile(delete=False)
            output_file.write(result.buffer.getvalue())
            output_file.close()
            logger.error('Dumped generated test image for debugging purposes: %s' % output_file.name)
            raise e

        expected_filesize = os.path.getsize(expected_path)
        generated_filesize = len(result.buffer.getvalue())

        ratio = generated_filesize / expected_filesize
        assert ratio <= size_tolerance, \
            'Generated file bigger than size tolerance: %f (should be <= %f)' % (ratio, size_tolerance)

        return result.buffer
