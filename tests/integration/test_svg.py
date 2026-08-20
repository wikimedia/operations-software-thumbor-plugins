import os.path
from unittest.mock import patch

from wikimedia_thumbor.shell_runner import ShellRunner

from . import WikimediaTestCase


class WikimediaSvgTest(WikimediaTestCase):
    def test_svg(self):
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:lang(fr):format(png)/Speech_bubbles.svg',
            mediawiki_reference_thumbnail='langfr-200px-Speech_bubbles.svg.png',
            perfect_reference_thumbnail='langfr-200px-Speech_bubbles.svg.png',
            expected_width=200,
            expected_height=148,
            expected_ssim=0.93,
            size_tolerance=0.81
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:lang(fr):format(webp)/Speech_bubbles.svg',
            mediawiki_reference_thumbnail='langfr-200px-Speech_bubbles.svg.png',
            perfect_reference_thumbnail='langfr-200px-Speech_bubbles.svg.png',
            expected_width=200,
            expected_height=148,
            expected_ssim=0.93,
            size_tolerance=0.55
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:format(png)/Television.svg',
            mediawiki_reference_thumbnail='200px-Television.svg.png',
            perfect_reference_thumbnail='200px-Television.svg.png',
            expected_width=200,
            expected_height=200,
            expected_ssim=0.99,
            size_tolerance=0.96
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:format(webp)/Television.svg',
            mediawiki_reference_thumbnail='200px-Television.svg.png',
            perfect_reference_thumbnail='200px-Television.svg.png',
            expected_width=200,
            expected_height=200,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            expected_ssim=0.99,
            size_tolerance=0.66
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:format(png)/Lori_in_Armenia.svg',
            mediawiki_reference_thumbnail='200px-Lori_in_Armenia.svg.png',
            perfect_reference_thumbnail='200px-Lori_in_Armenia.svg.png',
            expected_width=200,
            expected_height=205,
            expected_ssim=0.94,
            size_tolerance=0.98
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/200x/filters:format(webp)/Lori_in_Armenia.svg',
            mediawiki_reference_thumbnail='200px-Lori_in_Armenia.svg.png',
            perfect_reference_thumbnail='200px-Lori_in_Armenia.svg.png',
            expected_width=200,
            expected_height=205,
            expected_ssim=0.94,
            size_tolerance=0.5
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(png)/Northumberland_in_England.svg',
            mediawiki_reference_thumbnail='400px-Northumberland_in_England.svg.png',
            perfect_reference_thumbnail='400px-Northumberland_in_England.svg.png',
            expected_width=400,
            expected_height=486,
            expected_ssim=0.98,
            size_tolerance=1.0
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Northumberland_in_England.svg',
            mediawiki_reference_thumbnail='400px-Northumberland_in_England.svg.png',
            perfect_reference_thumbnail='400px-Northumberland_in_England.svg.png',
            expected_width=400,
            expected_height=486,
            expected_ssim=0.98,
            size_tolerance=0.5
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(png)/Map_of_the_Beboid_languages.svg',
            mediawiki_reference_thumbnail='400px-Map_of_the_Beboid_languages.svg.png',
            perfect_reference_thumbnail='400px-Map_of_the_Beboid_languages.svg.png',
            expected_width=400,
            expected_height=250,
            expected_ssim=0.85,
            size_tolerance=1.1
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Map_of_the_Beboid_languages.svg',
            mediawiki_reference_thumbnail='400px-Map_of_the_Beboid_languages.svg.png',
            perfect_reference_thumbnail='400px-Map_of_the_Beboid_languages.svg.png',
            expected_width=400,
            expected_height=250,
            expected_ssim=0.85,
            size_tolerance=0.86
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(png)/Westmoreland_Heritage_Trail.svg',
            mediawiki_reference_thumbnail='400px-Westmoreland_Heritage_Trail.svg.png',
            perfect_reference_thumbnail='400px-Westmoreland_Heritage_Trail.svg.png',
            expected_width=400,
            expected_height=161,
            expected_ssim=0.99,
            size_tolerance=0.999
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Westmoreland_Heritage_Trail.svg',
            mediawiki_reference_thumbnail='400px-Westmoreland_Heritage_Trail.svg.png',
            perfect_reference_thumbnail='400px-Westmoreland_Heritage_Trail.svg.png',
            expected_width=400,
            expected_height=161,
            expected_ssim=0.99,
            size_tolerance=0.63
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(png)/Tree_edges.svg',
            mediawiki_reference_thumbnail='400px-Tree_edges.svg.png',
            perfect_reference_thumbnail='400px-Tree_edges.svg.png',
            expected_width=400,
            expected_height=238,
            expected_ssim=0.95,
            size_tolerance=1.2
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/400x/filters:format(webp)/Tree_edges.svg',
            mediawiki_reference_thumbnail='400px-Tree_edges.svg.png',
            perfect_reference_thumbnail='400px-Tree_edges.svg.png',
            expected_width=400,
            expected_height=238,
            expected_ssim=0.95,
            size_tolerance=0.73
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/119x/filters:format(png)/BuickLogo_silber.svg',
            mediawiki_reference_thumbnail='119px-BuickLogo_silber.svg.png',
            perfect_reference_thumbnail='119px-BuickLogo_silber.svg.png',
            expected_width=119,
            expected_height=120,
            expected_ssim=0.95,
            size_tolerance=0.99
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/119x/filters:format(webp)/BuickLogo_silber.svg',
            mediawiki_reference_thumbnail='119px-BuickLogo_silber.svg.png',
            perfect_reference_thumbnail='119px-BuickLogo_silber.svg.png',
            expected_width=119,
            expected_height=120,
            # WebP compresses the alpha layer more agressively by default, which results in this
            # low score. This can be avoided in webp >= 0.5 with the -exact function, currently
            # only available on Debian Stretch.
            expected_ssim=0.95,
            size_tolerance=0.67
        )
        self.run_and_check_ssim_and_size(
            '/thumbor/unsafe/640x/filters:format(png)/IPv6_header-en.svg',
            mediawiki_reference_thumbnail='IPv6_header-langaz.svg.png',
            perfect_reference_thumbnail='IPv6_header-langaz.svg.png',
            expected_width=640,
            expected_height=295,
            expected_ssim=0.99,
            size_tolerance=1.5,
            headers={"lang": "az"}
        )

    def test_lang_variant_not_stripped(self):
        # Ensure that language codes get passed to rsvg-convert properly
        commands = []
        original_popen = ShellRunner.popen

        def record_popen(command, context, env=None):
            commands.append(command)
            return original_popen(command, context, env)

        with patch.object(ShellRunner, 'popen', record_popen):
            result = self.fetch(
                '/thumbor/unsafe/200x/filters:lang(sr-latn):format(png)/Speech_bubbles.svg'
            )

        assert result.code == 200, 'Response code: %s' % result.code

        rsvg_commands = [
            command for command in commands
            if os.path.basename(command[0]) == 'rsvg-convert'
        ]

        assert rsvg_commands, 'rsvg-convert was never called: %r' % commands

        for command in rsvg_commands:
            assert '--accept-language' in command, \
                'No language passed to rsvg-convert: %r' % command

            passed_lang = command[command.index('--accept-language') + 1]

            assert passed_lang == 'sr-latn', \
                'Language tag altered: %s (should be sr-latn)' % passed_lang
