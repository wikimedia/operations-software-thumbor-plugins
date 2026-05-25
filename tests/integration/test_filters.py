from . import WikimediaTestCase


class WikimediaFiltersTest(WikimediaTestCase):
    def test_crop(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:crop(10,10,20,20)/1Mcolors.png',
            mediawiki_reference_thumbnail='crop-1Mcolors.png',
            perfect_reference_thumbnail='crop-1Mcolors.png',
            expected_width=10,
            expected_height=10,
            expected_ssim=0.98,
            size_tolerance=1.0
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:crop(10,10,20,20):format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='crop-1Mcolors.png',
            perfect_reference_thumbnail='crop-1Mcolors.png',
            expected_width=10,
            expected_height=10,
            expected_ssim=0.98,
            size_tolerance=0.25
        )

    def test_flip_x(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:flip(x)/1Mcolors.png',
            mediawiki_reference_thumbnail='flipx-1Mcolors.png',
            perfect_reference_thumbnail='flipx-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.89
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:flip(x):format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='flipx-1Mcolors.png',
            perfect_reference_thumbnail='flipx-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.22
        )

    def test_flip_y(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:flip(y)/1Mcolors.png',
            mediawiki_reference_thumbnail='flipy-1Mcolors.png',
            perfect_reference_thumbnail='flipy-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.87
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:flip(y):format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='flipy-1Mcolors.png',
            perfect_reference_thumbnail='flipy-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.22
        )

    def test_rotate(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/filters:rotate(90)/1Mcolors.png',
            mediawiki_reference_thumbnail='rot90deg-1Mcolors.png',
            perfect_reference_thumbnail='rot90deg-1Mcolors.png',
            expected_width=1000,
            expected_height=1000,
            expected_ssim=0.99,
            size_tolerance=0.4
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/filters:rotate(90):format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='rot90deg-1Mcolors.png',
            perfect_reference_thumbnail='rot90deg-1Mcolors.png',
            expected_width=1000,
            expected_height=1000,
            expected_ssim=0.99,
            size_tolerance=0.04
        )

    def test_no_filter(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/1Mcolors.png',
            mediawiki_reference_thumbnail='1Mcolors.png',
            perfect_reference_thumbnail='1Mcolors.png',
            expected_width=1000,
            expected_height=1000,
            expected_ssim=1.0,
            size_tolerance=1.5
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/filters:format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='1Mcolors.png',
            perfect_reference_thumbnail='1Mcolors.png',
            expected_width=1000,
            expected_height=1000,
            expected_ssim=1.0,
            size_tolerance=0.62
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/Tower.jpg',
            mediawiki_reference_thumbnail='Tower.jpg',
            perfect_reference_thumbnail='Tower.jpg',
            expected_width=1456,
            expected_height=2592,
            expected_ssim=0.98,
            size_tolerance=0.53
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/filters:format(webp)/Tower.jpg',
            mediawiki_reference_thumbnail='Tower.jpg',
            perfect_reference_thumbnail='Tower.jpg',
            expected_width=1456,
            expected_height=2592,
            expected_ssim=0.97,
            size_tolerance=0.37
        )
