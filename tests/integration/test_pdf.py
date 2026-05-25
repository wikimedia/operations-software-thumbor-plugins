import pytest
import logging
from shutil import which
from . import WikimediaTestCase


class WikimediaPdfTest(WikimediaTestCase):
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
            mediawiki_reference_thumbnail='page3-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page3-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.92,
            size_tolerance=0.55,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(3):format(webp)/Internationalisation.pdf',
            mediawiki_reference_thumbnail='page3-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page3-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.93,
            size_tolerance=0.62,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(19)/Jeremy_Bentham.pdf',
            mediawiki_reference_thumbnail='page19-400px-Jeremy_Bentham.pdf.jpg',
            perfect_reference_thumbnail='page19-400px-Jeremy_Bentham.pdf.png',
            expected_width=400,
            expected_height=673,
            expected_ssim=0.96,
            size_tolerance=0.55,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(19):format(webp)/Jeremy_Bentham.pdf',
            mediawiki_reference_thumbnail='page19-400px-Jeremy_Bentham.pdf.jpg',
            perfect_reference_thumbnail='page19-400px-Jeremy_Bentham.pdf.png',
            expected_width=400,
            expected_height=673,
            expected_ssim=0.96,
            size_tolerance=0.42,
        )

    def test_pdf_without_page_filter(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/Internationalisation.pdf',
            mediawiki_reference_thumbnail='page1-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.92,
            size_tolerance=0.54,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Internationalisation.pdf',
            mediawiki_reference_thumbnail='page1-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.93,
            size_tolerance=0.6,
        )

    def test_pdf_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500)/Internationalisation.pdf',
            mediawiki_reference_thumbnail='page1-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.92,
            size_tolerance=0.54,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500):format(webp)/Internationalisation.pdf',
            mediawiki_reference_thumbnail='page1-400px-Internationalisation.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-Internationalisation.pdf.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.93,
            size_tolerance=0.6,
        )

    def test_pdf_nonfatal_gs_errors(self):
        """Regression test for T236240"""
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/18KOZ-1.pdf',
            mediawiki_reference_thumbnail='page1-400px-18KOZ-1.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-18KOZ-1.pdf.png',
            expected_width=400,
            expected_height=566,
            expected_ssim=0.9,
            size_tolerance=0.63,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/18KOZ-1.pdf',
            mediawiki_reference_thumbnail='page1-400px-18KOZ-1.pdf.jpg',
            perfect_reference_thumbnail='page1-400px-18KOZ-1.pdf.png',
            expected_width=400,
            expected_height=566,
            expected_ssim=0.9,
            size_tolerance=0.6,
        )

    @pytest.mark.usefixtures("inject_fixtures")
    def test_gs_commanderror_raise(self):
        with self.caplog.at_level(logging.ERROR):
            url = '/thumbor/unsafe/18KOZ-1.pdf'
            result = self.fetch(url)

            assert result.code == 500
            assert "CommandError: ([\'wrong/path\'" in self.caplog.text
