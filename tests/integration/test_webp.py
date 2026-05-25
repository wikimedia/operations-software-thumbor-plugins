from . import WikimediaTestCase


class WikimediaWebpTest(WikimediaTestCase):
    def test_webp(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/filters:format(png)/Album_en_blanco_y_negro.webp',
            mediawiki_reference_thumbnail='300px-Album_en_blanco_y_negro.webp.png',
            perfect_reference_thumbnail='300px-Album_en_blanco_y_negro.webp.png',
            expected_width=300,
            expected_height=202,
            expected_ssim=0.99,
            size_tolerance=1.06
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/filters:format(webp)/Album_en_blanco_y_negro.webp',
            mediawiki_reference_thumbnail='300px-Album_en_blanco_y_negro.webp.png',
            perfect_reference_thumbnail='300px-Album_en_blanco_y_negro.webp.png',
            expected_width=300,
            expected_height=202,
            expected_ssim=0.97,
            size_tolerance=0.14
        )
