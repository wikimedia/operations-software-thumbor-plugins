from . import WikimediaTestCase


class WikimediaProxyLoaderTest(WikimediaTestCase):
    def get_config(self):
        cfg = super(WikimediaProxyLoaderTest, self).get_config()
        cfg.LOADER = 'wikimedia_thumbor.loader.proxy'
        cfg.PROXY_LOADER_LOADERS = [
            'wikimedia_thumbor.loader.video'
        ]
        return cfg

    def test_proxied_video(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/320x/filters:page(1)/https://upload.wikimedia.org/wikipedia/commons/a/a3/Aequipotentialflaechen.webm',
            mediawiki_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.jpg',
            perfect_reference_thumbnail='320px-seek=1-Aequipotentialflaechen.webm.png',
            expected_width=320,
            expected_height=240,
            expected_ssim=0.99,
            size_tolerance=0.81
        )

    def test_proxied_png(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/https://upload.wikimedia.org/wikipedia/commons/d/d6/1Mcolors.png',
            mediawiki_reference_thumbnail='400px-1Mcolors.png',
            perfect_reference_thumbnail='400px-1Mcolors.png',
            expected_width=400,
            expected_height=400,
            expected_ssim=0.99,
            size_tolerance=0.75
        )

    def test_proxied_gif(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/300x/https://upload.wikimedia.org/wikipedia/commons/f/fb/Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            mediawiki_reference_thumbnail='300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            perfect_reference_thumbnail='300px-Pacific-Electric-Red-Cars-Awaiting-Destruction.gif',
            expected_width=300,
            expected_height=187,
            expected_ssim=0.98,
            size_tolerance=1.11
        )
