import hashlib
import json
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from thumbor.config import Config
from thumbor.context import Context

from wikimedia_thumbor.engine.vips.vips import Engine

JPEG_HEADER = b"\xff\xd8\xff\xe0"
PNG_HEADER = b"\x89PNG\r\n\x1a\n"

# md5("Cat1.jpg") starts with an "a", md5("Dog.jpg") does not
IN_BUCKET = "Cat1.jpg"
OUT_OF_BUCKET = "Dog.jpg"


def should_run(buffer, filename, size="8000x8000", min_pixels=20000000, rollout_hex=("a",)):
    """Ask the VIPS engine whether it wants to handle this original."""
    context = Context(config=Config(VIPS_ENGINE_MIN_PIXELS=min_pixels, VIPS_ENGINE_JPG_ROLLOUT_HEX=rollout_hex))
    context.request = SimpleNamespace(image_url="/foo/" + filename)
    context.wikimedia_original_filepath = "a/ab/" + filename

    engine = Engine(context)
    exiftool = SimpleNamespace(command=lambda **kw: json.dumps([{"ImageSize": size}]).encode())

    with patch.object(Engine, "exiftool", exiftool):
        return engine.should_run(buffer)


class TestPixelThreshold:
    def test_large_png_runs(self):
        assert should_run(PNG_HEADER, "WorldMap.png") is True

    def test_small_png_does_not_run(self):
        assert should_run(PNG_HEADER, "WorldMap.png", size="100x100") is False

    def test_small_jpg_does_not_run_even_when_in_the_bucket(self):
        assert should_run(JPEG_HEADER, IN_BUCKET, size="100x100") is False


class TestJpgRollout:
    def test_large_jpg_runs_when_the_filename_hashes_into_the_bucket(self):
        assert should_run(JPEG_HEADER, IN_BUCKET) is True

    def test_large_jpg_does_not_run_otherwise(self):
        assert should_run(JPEG_HEADER, OUT_OF_BUCKET) is False

    def test_the_bucket_does_not_apply_to_other_formats(self):
        assert should_run(PNG_HEADER, "Dog.png") is True

    def test_an_empty_prefix_lets_every_jpg_through(self):
        assert should_run(JPEG_HEADER, OUT_OF_BUCKET, rollout_hex=[""]) is True

    def test_no_prefixes_keeps_every_jpg_out(self):
        assert should_run(JPEG_HEADER, IN_BUCKET, rollout_hex=[]) is False

    def test_the_bucket_is_configurable(self):
        digest = hashlib.md5(OUT_OF_BUCKET.encode("utf-8")).hexdigest()

        assert should_run(JPEG_HEADER, OUT_OF_BUCKET, rollout_hex=[digest[:2]]) is True
        assert should_run(JPEG_HEADER, IN_BUCKET, rollout_hex=[digest[:2]]) is False

    def test_several_buckets_can_be_configured(self):
        digest = hashlib.md5(OUT_OF_BUCKET.encode("utf-8")).hexdigest()

        assert should_run(JPEG_HEADER, OUT_OF_BUCKET, rollout_hex=["a", digest[:2]]) is True
        assert should_run(JPEG_HEADER, IN_BUCKET, rollout_hex=["a", digest[:2]]) is True

    def test_filename_comes_from_the_url_without_an_original_filepath(self):
        context = Context(config=Config(VIPS_ENGINE_MIN_PIXELS=0, VIPS_ENGINE_JPG_ROLLOUT_HEX=["a"]))
        context.request = SimpleNamespace(image_url="https://upload.example/foo/" + IN_BUCKET)

        engine = Engine(context)

        assert engine.original_filename() == IN_BUCKET


@pytest.mark.parametrize("name,expected", [(IN_BUCKET, True), (OUT_OF_BUCKET, False)])
def test_bucket_fixtures_hash_as_expected(name, expected):
    # Guards the test data itself: if these hashes ever drift, the rollout
    # tests above would silently stop testing anything.
    assert hashlib.md5(name.encode("utf-8")).hexdigest().startswith("a") is expected
