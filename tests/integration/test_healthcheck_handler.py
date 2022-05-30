from thumbor.config import Config


from . import WikimediaTestCase


class WikimediaHealthcheckHandlerTestCase(WikimediaTestCase):
    def get_config(self):
        cfg = Config(SECURITY_KEY='ACME-SEC')

        cfg.COMMUNITY_EXTENSIONS = [
            'wikimedia_thumbor.handler.healthcheck'
        ]

        return cfg

    def test_healthcheck(self):
        response = self.fetch('/healthcheck')

        assert response.code == 200, 'Unexpected response code: %r' % response.code
        assert response.body == b'WORKING', 'Unexpected response body: %r' % response.body
