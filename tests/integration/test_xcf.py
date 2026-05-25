from . import WikimediaTestCase


class WikimediaXcfTest(WikimediaTestCase):
    def test_xcf(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(png)/Janus.xcf',
            mediawiki_reference_thumbnail='400px-Janus.xcf.png',
            perfect_reference_thumbnail='400px-Janus.xcf.png',
            expected_width=400,
            expected_height=431,
            # Compression/sharpening artifacts explain the SSIM difference, but
            # it's impossible to say when eyeballing if one if higher quality
            # than the other
            expected_ssim=0.92,
            size_tolerance=1.01
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Janus.xcf',
            mediawiki_reference_thumbnail='400px-Janus.xcf.png',
            perfect_reference_thumbnail='400px-Janus.xcf.png',
            expected_width=400,
            expected_height=431,
            expected_ssim=0.92,
            size_tolerance=0.68
        )
