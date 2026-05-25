import platform
import pytest

from . import WikimediaTestCase


class WikimediaPngTest(WikimediaTestCase):
    def test_png(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/1Mcolors.png',
            mediawiki_reference_thumbnail='400px-1Mcolors.png',
            perfect_reference_thumbnail='400px-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.74
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/1Mcolors.png',
            mediawiki_reference_thumbnail='400px-1Mcolors.png',
            perfect_reference_thumbnail='400px-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.2
        )

    def test_broken(self):
        # That file only works with recent versions of ImageMagick
        # Our production version doesn't support it yet
        if platform.system() != 'Darwin':
            pytest.skip("Didn't support another system yet")

        # T179200 Partially broken PNG
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/Nokia_3310_2017_DS.png',
            mediawiki_reference_thumbnail='400px-Nokia_3310_2017_DS.png',
            perfect_reference_thumbnail='400px-Nokia_3310_2017_DS.png',
            expected_width=400,
            expected_height=901,
            expected_ssim=0.99,
            size_tolerance=1.1
        )

    def test_transparent(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/' +
            'PNG_transparency_demonstration_1.png',
            mediawiki_reference_thumbnail='400px-PNG_transparency_demonstration_1.png',
            perfect_reference_thumbnail='400px-PNG_transparency_demonstration_1.png',
            expected_width=400,
            expected_height=300,
            expected_ssim=0.97,
            size_tolerance=1.1
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/' +
            'PNG_transparency_demonstration_1.png',
            mediawiki_reference_thumbnail='400px-PNG_transparency_demonstration_1.png',
            perfect_reference_thumbnail='400px-PNG_transparency_demonstration_1.png',
            expected_width=400,
            expected_height=300,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            expected_ssim=0.97,
            size_tolerance=0.68
        )
        # Palette PNG
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/' +
            'Cincinnati_Bell_logo.png',
            mediawiki_reference_thumbnail='400px-Cincinnati_Bell_logo.png',
            perfect_reference_thumbnail='400px-Cincinnati_Bell_logo.png',
            expected_width=400,
            expected_height=86,
            # Likely due to differences compressing the transparency layer between IM versions
            expected_ssim=0.75,
            # The thumbnail is bigger because ImageMagick either messes with the palette if we ask it
            # to generate a palette PNG via the PNG8 output, making the image ugly and aliased (but small)
            # or, as it does automatically here, converts the output to an RGBA image and conserves fidelity
            size_tolerance=1.13
        )
        # Greyscale with alpha
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/' +
            'Quillette.png',
            mediawiki_reference_thumbnail='400px-Quillette.png',
            perfect_reference_thumbnail='400px-Quillette.png',
            expected_width=400,
            expected_height=100,
            expected_ssim=0.99,
            size_tolerance=1.01
        )
        # RGB with tRNS and no alpha channel
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/100x/' +
            'RGB_with_tRNS.png',
            mediawiki_reference_thumbnail='100px-RGB_with_tRNS.png',
            perfect_reference_thumbnail='100px-RGB_with_tRNS.png',
            expected_width=100,
            expected_height=100,
            expected_ssim=0.99,
            size_tolerance=1.0
        )
        # Greyscale with tRNS and no alpha channel
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/100x/' +
            'Greyscale_with_tRNS.png',
            mediawiki_reference_thumbnail='100px-Greyscale_with_tRNS.png',
            perfect_reference_thumbnail='100px-Greyscale_with_tRNS.png',
            expected_width=100,
            expected_height=100,
            expected_ssim=0.99,
            size_tolerance=1.0
        )

    def test_T245440(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/Ethiopian_Region_Map_with_Capitals_and_Flags.png',
            mediawiki_reference_thumbnail='400px-Ethiopian_Region_Map_with_Capitals_and_Flags.png',
            perfect_reference_thumbnail='400px-Ethiopian_Region_Map_with_Capitals_and_Flags.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.9,
            size_tolerance=1.0,
        )
