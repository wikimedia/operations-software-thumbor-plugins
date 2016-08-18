import os
import subprocess
import tempfile

from . import WikimediaTestCase


class WikimediaExifTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaExifTest, self).get_config()
        cfg.EXIFTOOL_STAY_OPEN = True
        return cfg

    def run_and_check_ssim_size_and_exif(
        self,
        url,
        expected,
        expected_ssim,
        size_tolerance,
        exif_fields
    ):
        """Request URL and check ssim, size and exif.

        Arguments:
        url -- thumbnail URL
        expected -- reference thumbnail file
        expected_ssim -- minimum SSIM score
        size_tolerance -- maximum file size ratio between reference and result
        exif_fields -- expected EXIF field values
        """
        result = super(WikimediaExifTest, self).run_and_check_ssim_and_size(
            url,
            expected,
            expected_ssim,
            size_tolerance
        )

        tmp = tempfile.NamedTemporaryFile(delete=False)
        tmp.write(result.buffer.read())
        tmp.close()

        for field in exif_fields:
            self.check_exif_field(tmp.name, field, exif_fields[field])

        os.remove(tmp.name)

    def check_exif_field(self, filename, field, expected):
        command = ['exiftool',  '-' + field, '-s', '-s', '-s', filename]
        result = subprocess.check_output(command).strip()

        assert result == expected, \
            'EXIF field %s: %s' % (field, result)

    def test_adobe_rgb(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/300x/filters:conditional_sharpen(0.6,0.01,false,0.85)/'
            + 'Physical_map_tagged_AdobeRGB.jpg',
            '300px-Physical_map_tagged_AdobeRGB.jpg',
            0.98,
            1.0,
            {
                'ProfileDescription': 'Adobe RGB (1998)'
            }
        )

    def test_exif_filtering(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/800x/filters:conditional_sharpen(0.6,0.01,false,0.85)/'
            + 'Munich_subway_station_Westfriedhof.jpg',
            '800px-Munich_subway_station_Westfriedhof.jpg',
            # The "low" score is due to the sharpening algorithm being
            # different between Mediawiki and Thumbor. Mediawiki generates
            # visual artifacts not seen in the Thumbor version
            0.93,
            1.0,
            {
                'Artist': 'Martin Falbisoner',
                'Copyright': 'some rights reserved',
                'ShootingMode': ''
            }
        )

    def test_exif_rotation(self):
        self.run_and_check_ssim_size_and_exif(
            'unsafe/40x/filters:conditional_sharpen(0.6,0.01,false,0.85)/'
            + 'EXIF_rotation_180.jpg',
            '40px-EXIF_rotation_180.jpg',
            0.99,
            1.1,
            {
                'Orientation': ''
            }
        )
