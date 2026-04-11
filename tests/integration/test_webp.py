import io
from PIL import Image
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

    def test_animated_webp(self):
        # Animated WebP should result in an animated WebP thumbnail.
        # animated.webp is 50x50.
        response = self.fetch('/thumbor/unsafe/25x/animated.webp')
        self.assertEqual(response.code, 200)
        img = Image.open(io.BytesIO(response.body))
        self.assertEqual(img.size, (25, 25))
        self.assertTrue(getattr(img, 'is_animated', False))
        self.assertEqual(img.format, 'WEBP')
        # Check frame count
        self.assertEqual(img.n_frames, 2)
