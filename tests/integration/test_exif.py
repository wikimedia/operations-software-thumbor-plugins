import logging
import os
import shutil
from fractions import Fraction
from PIL import Image
from tempfile import NamedTemporaryFile
from pyexiv2 import ImageMetadata
from wikimedia_thumbor.shell_runner import ShellRunner

from . import WikimediaTestCase


class WikimediaExifTest(WikimediaTestCase):
    def run_and_check_exif(
        self,
        url,
        expected_exif_fields,
        expected_icc_profile
    ):
        """Request URL and check ssim, size and exif.

        Arguments:
        url -- thumbnail URL
        expected_exif_fields -- expected EXIF field values
        expected_icc_profile -- expected ICC profile
        """
        result_buffer = self.fetch(url)

        result = Image.open(result_buffer)

        if expected_exif_fields:
            self.check_exif(result_buffer, expected_exif_fields)

        if expected_icc_profile:
            assert result.info['icc_profile'] == expected_icc_profile, \
                'ICC profile: %s' % result.info['icc_profile']

    def check_exif(self, result_buffer, expected):
        temp_file = NamedTemporaryFile(delete=False)

        result_buffer.seek(0)
        with open(temp_file.name, 'wb') as f:
            shutil.copyfileobj(result_buffer, f)

        metadata = ImageMetadata(temp_file.name)
        logging.disable(logging.ERROR)
        metadata.read()
        logging.disable(logging.NOTSET)

        ShellRunner.rm_f(temp_file.name)

        found = {}

        for field in metadata.exif_keys:
            found[field] = metadata.get(field).value

        assert found == expected, 'EXIF fields mismatch. Expected: %r Found: %r' % (expected, found)

    def test_adobe_rgb(self):
        adobe_rgb = (
            '\x00\x00\x02HADBE\x02\x10\x00\x00mntrRGB XYZ \x07\xcf\x00\x06\x00'
            + '\x03\x00\x00\x00\x00\x00\x00acspMSFT\x00\x00\x00\x00none\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01'
            + '\x00\x00\xf6\xd6\x00\x01\x00\x00\x00\x00\xd3-ADBE\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\ncprt\x00\x00\x00\xfc\x00\x00\x00Ldesc\x00\x00\x01H\x00\x00'
            + '\x00kwtpt\x00\x00\x01\xb4\x00\x00\x00\x14bkpt\x00\x00\x01\xc8'
            + '\x00\x00\x00\x14rTRC\x00\x00\x01\xdc\x00\x00\x00\x0egTRC\x00'
            + '\x00\x01\xec\x00\x00\x00\x0ebTRC\x00\x00\x01\xfc\x00\x00\x00'
            + '\x0erXYZ\x00\x00\x02\x0c\x00\x00\x00\x14gXYZ\x00\x00\x02 \x00'
            + '\x00\x00\x14bXYZ\x00\x00\x024\x00\x00\x00\x14text\x00\x00\x00'
            + '\x00Copyright (c) 1999 Adobe Systems Incorporated. All Rights '
            + 'Reserved.\x00desc\x00\x00\x00\x00\x00\x00\x00\x11Adobe RGB '
            + '(1998)\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00XYZ \x00\x00\x00\x00\x00\x00\xf3Q\x00'
            + '\x01\x00\x00\x00\x01\x16\xccXYZ \x00\x00\x00\x00\x00\x00\x00'
            + '\x00\x00\x00\x00\x00\x00\x00\x00\x00curv\x00\x00\x00\x00\x00'
            + '\x00\x00\x01\x023\x00\x00curv\x00\x00\x00\x00\x00\x00\x00\x01'
            + '\x023\x00\x00curv\x00\x00\x00\x00\x00\x00\x00\x01\x023\x00'
            + '\x00XYZ \x00\x00\x00\x00\x00\x00\x9c\x18\x00\x00O\xa5\x00\x00'
            + '\x04\xfcXYZ \x00\x00\x00\x00\x00\x004\x8d\x00\x00\xa0,\x00\x00'
            + '\x0f\x95XYZ \x00\x00\x00\x00\x00\x00&1\x00\x00\x10/\x00\x00'
            + '\xbe\x9c'
        )

        self.run_and_check_exif(
            'thumbor/unsafe/300x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/Physical_map_tagged_AdobeRGB.jpg',
            None,
            adobe_rgb
        )
        self.run_and_check_exif(
            'thumbor/unsafe/300x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(webp)/Physical_map_tagged_AdobeRGB.jpg',
            None,
            adobe_rgb
        )

    def test_exif_filtering(self):
        self.run_and_check_exif(
            'thumbor/unsafe/800x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/Munich_subway_station_Westfriedhof.jpg',
            {
                'Exif.Image.YCbCrPositioning': 1,
                'Exif.Image.Copyright': 'some rights reserved',
                'Exif.Image.XResolution': Fraction(72, 1),
                'Exif.Image.Artist': 'Martin Falbisoner',
                'Exif.Image.YResolution': Fraction(72, 1),
                'Exif.Image.ResolutionUnit': 2
            },
            None
        )
        self.run_and_check_exif(
            'thumbor/unsafe/800x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(webp)/Munich_subway_station_Westfriedhof.jpg',
            {
                'Exif.Image.YCbCrPositioning': 1,
                'Exif.Image.Copyright': 'some rights reserved',
                'Exif.Image.XResolution': Fraction(72, 1),
                'Exif.Image.Artist': 'Martin Falbisoner',
                'Exif.Image.YResolution': Fraction(72, 1),
                'Exif.Image.ResolutionUnit': 2
            },
            None
        )

    def test_tinyrgb_substitution(self):
        tinyrgb_path = os.path.join(
            os.path.dirname(__file__),
            'tinyrgb.icc'
        )
        with open(tinyrgb_path, 'r') as tinyrgb_file:
            tinyrgb = tinyrgb_file.read()

        self.run_and_check_exif(
            'thumbor/unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85)/Christophe_Henner_-_June_2016.JPG',
            None,
            tinyrgb
        )
        self.run_and_check_exif(
            'thumbor/unsafe/400x/filters:conditional_sharpen(0.0,0.8,1.0,0.0,0.85):format(webp)/Christophe_Henner_-_June_2016.JPG',
            None,
            tinyrgb
        )
