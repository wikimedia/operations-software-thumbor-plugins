import os
from swiftclient.client import Connection
from swiftclient.exceptions import ClientException
from thumbor.config import Config
from tornado.simple_httpclient import SimpleAsyncHTTPClient
from tornado.httpclient import HTTPResponse


from . import WikimediaTestCase


class WikimediaSwiftTestCase(WikimediaTestCase):
    def setUp(self):
        super(WikimediaSwiftTestCase, self).setUp()

        self.original_fetch_impl = SimpleAsyncHTTPClient.fetch_impl

        def fetch_impl(self, request, callback):
            expected = 'http://swifthost/swift/v1/api/path/' \
                + 'wikipedia-en-local-public/d/d3/1Mcolors.png'

            if request.request.url == expected:
                path = os.path.join(
                    os.path.dirname(__file__),
                    'originals',
                    '1Mcolors.png'
                )
                with open(path, 'rb') as f:
                    body = f.read()

                callback(HTTPResponse(request, 200, buffer=body))
            else:
                callback(HTTPResponse(request, 404))

        SimpleAsyncHTTPClient.fetch_impl = fetch_impl

        self.original_put_object = Connection.put_object
        Connection.put_object = self.mock_put_object
        self.put_object_calls = 0

        self.original_get_object = Connection.get_object
        Connection.get_object = self.mock_get_object
        self.get_object_calls = 0

    def tearDown(self):
        super(WikimediaSwiftTestCase, self).tearDown()
        SimpleAsyncHTTPClient.fetch_impl = self.original_fetch_impl
        Connection.get_object = self.original_get_object
        Connection.put_object = self.original_put_object

    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.images'
        ]

        cfg.STORAGE = 'wikimedia_thumbor.storage.request'
        cfg.RESULT_STORAGE = 'wikimedia_thumbor.result_storage.swift'
        cfg.RESULT_STORAGE_STORES_UNSAFE = True
        cfg.SWIFT_HOST = 'http://swifthost'
        cfg.SWIFT_API_PATH = '/swift/v1/api/path'
        cfg.SWIFT_AUTH_PATH = '/auth/v1.0'
        cfg.SWIFT_USER = 'foo:bar'
        cfg.SWIFT_KEY = 'baz'
        cfg.SWIFT_SHARDED_CONTAINERS = [
            'wikipedia-en-local-public',
            'wikipedia-en-local-thumb'
        ]
        cfg.SWIFT_PATH_PREFIX = 'thumbor/'
        cfg.SWIFT_CONNECTION_TIMEOUT = 1
        cfg.SWIFT_RETRIES = 0

        cfg.QUALITY_LOW = 10
        cfg.DEFAULT_FILTERS_JPEG = 'conditional_sharpen(0.0,0.8,1.0,0.0,0.85)'
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.PROXY_LOADER_LOADERS = ['wikimedia_thumbor.loader.swift']
        cfg.LOADER_EXCERPT_LENGTH = 4096
        cfg.HTTP_LOADER_TEMP_FILE_TIMEOUT = 10
        cfg.SWIFT_THUMBNAIL_EXPIRY_SECONDS = 60
        cfg.SWIFT_THUMBNAIL_EXPIRY_SAMPLING_FACTOR = 1

        return cfg

    def mock_put_object(self, container, obj, contents, content_length=None,
                        etag=None, chunk_size=None, content_type=None,
                        headers=None, query_string=None, response_dict=None):
        self.put_object_calls += 1

        assert container == 'wikipedia-en-local-thumb.d3', \
            'Unexpected swift container: %r' % container
        assert obj == 'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png', \
            'Unexpected swift obj: %r' % obj
        assert headers == {'Content-Disposition': 'inline;filename*=UTF-8\'\'1Mcolors.png', 'Xkey': 'File:1Mcolors.png', 'X-Delete-After': 60}, \
            'Unexpected swift headers: %r' % headers

    def mock_get_object(self, container, obj, resp_chunk_size=None,
                        query_string=None, response_dict=None, headers=None):
        self.get_object_calls += 1

        if self.get_object_calls == 1:
            assert container == 'wikipedia-en-local-thumb.d3', \
                'Unexpected swift container: %r' % container
            assert obj == 'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png', \
                'Unexpected swift obj: %r' % obj

            raise ClientException('Object not found')
        elif self.get_object_calls == 2:
            assert container == 'wikipedia-en-local-public.d3', \
                'Unexpected swift container: %r' % container
            assert obj == 'd/d3/1Mcolors.png', \
                'Unexpected swift obj: %r' % obj

            path = os.path.join(
                os.path.dirname(__file__),
                'originals',
                '1Mcolors.png'
            )
            with open(path, 'rb') as f:
                return {}, f.read()
        else:
            assert container == 'wikipedia-en-local-thumb.d3', \
                'Unexpected swift container: %r' % container
            assert obj == 'thumbor/d/d3/1Mcolors.png/400px-1Mcolors.png', \
                'Unexpected swift obj: %r' % obj

            path = os.path.join(
                os.path.dirname(__file__),
                'thumbnails',
                '400px-1Mcolors.png'
            )
            with open(path, 'rb') as f:
                return {}, f.read()

    def test_swift(self):
        # Thumbnail doesn't exist yet
        self.fetch(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png'
        )
        # Thumbnail exists now
        self.fetch(
            '/wikipedia/en/thumb/d/d3/1Mcolors.png/400px-1Mcolors.png'
        )
