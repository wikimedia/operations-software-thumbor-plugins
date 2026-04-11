from . import WikimediaTestCase


class OrientationTest(WikimediaTestCase):
    def test_orientations(self):
        for i in range(1, 9):
            # All orientations should result in the same 150x200 image as orient_1.jpg
            # (within some reasonable tolerance for JPEG encoding differences after reorientation)
            self.run_and_check_ssim_and_size(
                '/thumbor/unsafe/150x/orient_%d.jpg' % i,
                '150px-orient_1.jpg',
                '150px-orient_1.png',
                150,
                200,
                0.99,  # Very high SSIM expected since they should be identical
                1.02,  # 2% size tolerance
            )
