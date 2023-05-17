import pytest
import logging
from shutil import which
from . import WikimediaTestCase


class WikimediaTest(WikimediaTestCase):
    @pytest.fixture
    def inject_fixtures(self, caplog, monkeypatch):
        self.caplog = caplog
        monkeypatch.setattr(
            'tests.integration.which',
            lambda cmd: 'wrong/path' if cmd == 'gs' else which(cmd)
        )

    def test_pdf(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(3)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            'page3-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.55,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(3):format(webp)/Internationalisation.pdf',
            'page3-400px-Internationalisation.pdf.jpg',
            'page3-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.62,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(19)/Jeremy_Bentham.pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            'page19-400px-Jeremy_Bentham.pdf.png',
            400,
            673,
            0.96,
            0.55,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(19):format(webp)/Jeremy_Bentham.pdf',
            'page19-400px-Jeremy_Bentham.pdf.jpg',
            'page19-400px-Jeremy_Bentham.pdf.png',
            400,
            673,
            0.96,
            0.42,
        )

    def test_pdf_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.54,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.6,
        )

    def test_pdf_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.92,
            0.54,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500):format(webp)/Internationalisation.pdf',
            'page1-400px-Internationalisation.pdf.jpg',
            'page1-400px-Internationalisation.pdf.png',
            400,
            300,
            0.93,
            0.6,
        )

    def test_pdf_nonfatal_gs_errors(self):
        """Regression test for T236240"""
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/18KOZ-1.pdf',
            'page1-400px-18KOZ-1.pdf.jpg',
            'page1-400px-18KOZ-1.pdf.png',
            400,
            566,
            0.9,
            0.63,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/18KOZ-1.pdf',
            'page1-400px-18KOZ-1.pdf.jpg',
            'page1-400px-18KOZ-1.pdf.png',
            400,
            566,
            0.9,
            0.6,
        )

    @pytest.mark.usefixtures("inject_fixtures")
    def test_gs_commanderror_raise(self):
        with self.caplog.at_level(logging.ERROR):
            url = '/thumbor/unsafe/18KOZ-1.pdf'
            result = self.fetch(url)

            assert result.code == 500
            assert "CommandError: ([\'wrong/path\'" in self.caplog.text
