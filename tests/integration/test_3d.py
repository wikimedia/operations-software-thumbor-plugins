import pytest
import logging
from shutil import which
from . import WikimediaTestCase


class Wikimedia3DTest(WikimediaTestCase):
    @pytest.fixture
    def inject_fixtures(self, caplog, monkeypatch):
        self.caplog = caplog
        monkeypatch.setattr(
            'tests.integration.which',
            lambda cmd: 'wrong/path' if cmd == 'xvfb-run' else which(cmd)
        )

    def test_stl_text(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/filters:format(png)/crystal-NEW.stl',
            mediawiki_reference_thumbnail='300px-crystal-NEW.stl.png',
            perfect_reference_thumbnail='300px-crystal-NEW.stl.png',
            expected_width=300,
            expected_height=225,
            expected_ssim=1,
            size_tolerance=1
        )

    def test_stl_bin(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/filters:format(png)/4x2brick_0.00interference.STL',
            mediawiki_reference_thumbnail='300px-4x2brick_0.00interference.stl.png',
            perfect_reference_thumbnail='300px-4x2brick_0.00interference.stl.png',
            expected_width=300,
            expected_height=225,
            expected_ssim=1,
            size_tolerance=1
        )

    @pytest.mark.usefixtures("inject_fixtures")
    def test_stl_commanderror_raise(self):
        with self.caplog.at_level(logging.ERROR):
            url = '/thumbor/unsafe/crystal-NEW.stl'
            result = self.fetch(url)

            assert result.code == 500
            assert "CommandError: ([\'wrong/path\'" in self.caplog.text
