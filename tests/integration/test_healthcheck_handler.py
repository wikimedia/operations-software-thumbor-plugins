from thumbor.config import Config

from . import WikimediaTestCase


class WikimediaHealthcheckHandlerTestCase(WikimediaTestCase):
    def get_config(self):
        cfg = Config(SECURITY_KEY="ACME-SEC")

        cfg.COMMUNITY_EXTENSIONS = ["wikimedia_thumbor.handler.healthcheck"]

        return cfg

    def test_healthcheck(self):
        response = self.fetch("/healthcheck")

        assert response.code == 200, f"Unexpected response code: {response.code!r}"
        assert response.body == b"WORKING", f"Unexpected response body: {response.body!r}"
