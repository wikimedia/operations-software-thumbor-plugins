from . import WikimediaTestCase


class WikimediaDjvuTest(WikimediaTestCase):
    def test_with_page(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(2)/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page2-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page2-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=576,
            expected_ssim=0.99,
            size_tolerance=1.01,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(2):format(webp)/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page2-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page2-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=576,
            expected_ssim=0.99,
            size_tolerance=0.84,
        )

    def test_without_page(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page1-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page1-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=561,
            expected_ssim=0.98,
            size_tolerance=1.11,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page1-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page1-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=561,
            expected_ssim=0.99,
            size_tolerance=0.9,
        )

    def test_with_out_of_bounds_page(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500)/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page259-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page259-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=619,
            expected_ssim=0.99,
            size_tolerance=1.05,
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:page(500):format(webp)/Il_cavallarizzo.djvu',
            mediawiki_reference_thumbnail='page259-400px-Il_cavallarizzo.djvu.jpg',
            perfect_reference_thumbnail='page259-400px-Il_cavallarizzo.djvu.png',
            expected_width=400,
            expected_height=619,
            expected_ssim=0.99,
            size_tolerance=0.84,
        )
