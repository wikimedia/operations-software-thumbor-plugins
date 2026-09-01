import hashlib
from types import SimpleNamespace

from thumbor.config import Config

from wikimedia_thumbor.handler.images.images import _counter_value, _mc, _mc_encode_key


def handler(**config):
    """A stand-in for the BaseHandler these functions are patched onto."""
    return SimpleNamespace(context=SimpleNamespace(config=Config(**config)))


class TestCounterValue:
    def test_decodes_the_bytes_pymemcache_returns(self):
        assert _counter_value(b'3') == 3

    def test_missing_key_stays_none(self):
        assert _counter_value(None) is None

    def test_corrupt_value_does_not_raise(self):
        # A bad value must not take down a thumbnail request.
        assert _counter_value(b'not a number') is None


class TestEncodeKey:
    def test_hashes_the_xkey(self):
        expected = hashlib.sha256(b'File:Foo.jpg').hexdigest()

        assert _mc_encode_key(handler(), 'File:Foo.jpg') == 'sha256:' + expected

    def test_applies_the_configured_prefix(self):
        key = _mc_encode_key(handler(FAILURE_THROTTLING_PREFIX='WMF:'), 'File:Foo.jpg')

        assert key.startswith('WMF:sha256:')

    def test_undecodable_names_do_not_raise(self):
        # Original names are not guaranteed to be valid UTF-8.
        assert _mc_encode_key(handler(), b'\xff\xfe') is not None


class TestClient:
    def test_no_client_without_config(self):
        assert _mc(handler()) is False

    def test_client_is_built_and_reused(self):
        self_ = handler(FAILURE_THROTTLING_MEMCACHE=['127.0.0.1:11211'])

        client = _mc(self_)

        assert client is not False
        assert _mc(self_) is client

    def test_client_tolerates_an_unreachable_server(self):
        # ignore_exc: a memcached outage must never surface as a thumbnail
        # error. Port 1 refuses connections.
        client = _mc(handler(FAILURE_THROTTLING_MEMCACHE=['127.0.0.1:1']))

        assert client.get('any-key') is None
        assert client.set('any-key', b'1', expire=60) is False
