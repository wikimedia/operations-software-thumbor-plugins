import os

from . import WikimediaTestCase


class WikimediaVideoTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaVideoTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.video'

        return cfg

    def test_ogv(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            '2010-07-14-Blitze-Zeitlupe-1-08.ogg'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/' + path,
            mediawiki_reference_thumbnail='640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.jpg',
            perfect_reference_thumbnail='640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.png',
            expected_width=640,
            expected_height=480,
            expected_ssim=0.98,
            size_tolerance=0.76
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.jpg',
            perfect_reference_thumbnail='640px--2010-07-14-Blitze-Zeitlupe-1-08.ogg.png',
            expected_width=640,
            expected_height=480,
            expected_ssim=0.97,
            size_tolerance=0.49
        )

    def test_webm(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Aequipotentialflaechen.webm'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/320x/' + path,
            mediawiki_reference_thumbnail='320px--Aequipotentialflaechen.webm.jpg',
            perfect_reference_thumbnail='320px--Aequipotentialflaechen.webm.png',
            expected_width=320,
            expected_height=240,
            expected_ssim=0.98,
            size_tolerance=0.99
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/320x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='320px--Aequipotentialflaechen.webm.jpg',
            perfect_reference_thumbnail='320px--Aequipotentialflaechen.webm.png',
            expected_width=320,
            expected_height=240,
            expected_ssim=0.99,
            size_tolerance=0.54
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Cape_Town_under_the_clouds.webm'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/' + path,
            mediawiki_reference_thumbnail='640px--Cape_Town_under_the_clouds.webm.jpg',
            perfect_reference_thumbnail='640px--Cape_Town_under_the_clouds.webm.png',
            expected_width=640,
            expected_height=361,
            expected_ssim=0.97,
            size_tolerance=0.77
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='640px--Cape_Town_under_the_clouds.webm.jpg',
            perfect_reference_thumbnail='640px--Cape_Town_under_the_clouds.webm.png',
            expected_width=640,
            expected_height=361,
            expected_ssim=0.96,
            size_tolerance=0.38
        )

        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/' + path,
            mediawiki_reference_thumbnail='640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.jpg',
            perfect_reference_thumbnail='640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.png',
            expected_width=640,
            expected_height=360,
            expected_ssim=0.98,
            size_tolerance=0.86
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.jpg',
            perfect_reference_thumbnail='640px--Debris_flow_-_22_juillet_2013_-_Crue_torrentielle_a_Saint_Julien_Montdenis.webm.png',
            expected_width=640,
            expected_height=360,
            expected_ssim=0.98,
            size_tolerance=0.48
        )

    def test_webm_with_seek(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Aequipotentialflaechen.webm'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/320x/filters:page(1)/' + path,
            mediawiki_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.jpg',
            perfect_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.png',
            expected_width=320,
            expected_height=240,
            expected_ssim=0.99,
            size_tolerance=0.81
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/320x/filters:format(webp):page(1)/' + path,
            mediawiki_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.jpg',
            perfect_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.png',
            expected_width=320,
            expected_height=240,
            expected_ssim=0.99,
            size_tolerance=0.41
        )

    def test_non_square_pixels(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Malta-cat.ogv'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/800x/' + path,
            mediawiki_reference_thumbnail='800px-Malta-cat.ogv.jpg',
            perfect_reference_thumbnail='800px-Malta-cat.ogv.png',
            expected_width=800,
            expected_height=450,
            expected_ssim=0.96,
            size_tolerance=0.85
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/800x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='800px-Malta-cat.ogv.jpg',
            perfect_reference_thumbnail='800px-Malta-cat.ogv.png',
            expected_width=800,
            expected_height=450,
            expected_ssim=0.94,
            size_tolerance=0.49
        )

    def test_mpeg1(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Visualization-pone.0014754.s006.mpg'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/' + path,
            mediawiki_reference_thumbnail='640px--Visualization-pone.0014754.s006.mpg.jpg',
            perfect_reference_thumbnail='640px--Visualization-pone.0014754.s006.mpg.png',
            expected_width=640,
            expected_height=513,
            expected_ssim=0.96,
            size_tolerance=0.75
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='640px--Visualization-pone.0014754.s006.mpg.jpg',
            perfect_reference_thumbnail='640px--Visualization-pone.0014754.s006.mpg.png',
            expected_width=640,
            expected_height=513,
            expected_ssim=0.96,
            size_tolerance=0.75
        )

    def test_mpeg2(self):
        path = os.path.join(
            os.path.dirname(__file__),
            'originals',
            'Folgers.mpg'
        )

        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/352x/' + path,
            mediawiki_reference_thumbnail='352px--Folgers.mpg.jpg',
            perfect_reference_thumbnail='352px--Folgers.mpg.png',
            expected_width=352,
            expected_height=264,
            expected_ssim=0.98,
            size_tolerance=0.79
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/352x/filters:format(webp)/' + path,
            mediawiki_reference_thumbnail='352px--Folgers.mpg.jpg',
            perfect_reference_thumbnail='352px--Folgers.mpg.png',
            expected_width=352,
            expected_height=264,
            expected_ssim=0.97,
            size_tolerance=0.79
        )
