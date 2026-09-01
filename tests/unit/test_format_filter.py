import asyncio
from types import SimpleNamespace

import pytest
from thumbor.config import Config
from thumbor.context import Context
from tornado.web import HTTPError

from wikimedia_thumbor.filter.format.format import Filter

Filter.pre_compile()


def run_filter(image_url, requested_format, **config):
    """Run the format filter over an original at image_url, as thumbor would.

    Returns the format the filter settled on, or raises whatever the filter
    raised.
    """
    context = Context(config=Config(**config))
    context.request = SimpleNamespace(image_url=image_url, format=None)

    asyncio.run(Filter(f"format({requested_format})", context).run())

    return context.request.format


class TestAllowedConversions:
    def test_svg_may_become_png(self):
        assert run_filter("/foo/Bar.svg", "png") == "png"

    def test_extension_case_is_ignored(self):
        assert run_filter("/foo/Bar.SVG", "PNG") == "png"

    def test_jpeg_original_is_normalised_to_jpg_for_the_check(self):
        assert run_filter("/foo/Bar.JPEG", "webp") == "webp"

    def test_requested_format_is_not_normalised_on_the_way_out(self):
        # jpe/jpeg are normalised to jpg to look the conversion up, but the
        # format handed downstream is whatever was asked for. Documenting
        # rather than endorsing: the two halves disagree on purpose or by
        # accident, and changing it is a behaviour change, not a cleanup.
        assert run_filter("/foo/Bar.JPEG", "jpe") == "jpe"

    def test_format_missing_from_the_matrix_is_unrestricted(self):
        # tiff has no entry, so any allowed output format goes.
        assert run_filter("/foo/Bar.tiff", "png") == "png"


class TestDeniedConversions:
    def test_png_may_not_become_jpg(self):
        with pytest.raises(HTTPError) as excinfo:
            run_filter("/foo/Bar.png", "jpg")

        assert excinfo.value.status_code == 400

    def test_audio_may_not_be_converted_at_all(self):
        # T354994: only ogg is thumbnailable; the rest deny everything.
        with pytest.raises(HTTPError):
            run_filter("/foo/Bar.mp3", "png")

    def test_mid_is_normalised_to_midi_before_the_check(self):
        with pytest.raises(HTTPError):
            run_filter("/foo/Bar.mid", "png")

    def test_matrix_is_configurable(self):
        with pytest.raises(HTTPError):
            run_filter("/foo/Bar.svg", "png", ALLOWED_CONVERSIONS={"svg": {"webp"}})


class TestDisallowedOutputFormats:
    def test_unknown_output_format_clears_the_format(self):
        # Not a denial: the request falls back to thumbor's default handling.
        assert run_filter("/foo/Bar.tiff", "tiff") is None
