from . import WikimediaTestCase


class WikimediaGifTest(WikimediaTestCase):
    def test_gif(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            mediawiki_reference_thumbnail='300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            perfect_reference_thumbnail='300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            expected_width=300,
            expected_height=187,
            expected_ssim=0.98,
            size_tolerance=1.11
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/Jokie.gif',
            mediawiki_reference_thumbnail='300px-Jokie.gif',
            perfect_reference_thumbnail='300px-Jokie.gif',
            expected_width=300,
            expected_height=290,
            expected_ssim=0.99,
            size_tolerance=1.11
        )
        # Animated GIF that triggers MAX_ANIMATED_GIF_AREA
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/Tranylcypromine3DanJ.gif',
            mediawiki_reference_thumbnail='300px-Tranylcypromine3DanJ.gif',
            perfect_reference_thumbnail='300px-Tranylcypromine3DanJ.gif',
            expected_width=300,
            expected_height=145,
            expected_ssim=0.99,
            size_tolerance=1.0
        )
