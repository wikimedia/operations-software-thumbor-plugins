import time
from types import SimpleNamespace

from thumbor.config import Config

from wikimedia_thumbor.result_storage.swift.swift import thumbnail_expiry

EXPIRY = 172800
# The jitter the storage adds on top of the configured expiry.
JITTER = 3600

EXPERIMENT = {
    "SWIFT_THUMBNAIL_EXPIRY_SECONDS": EXPIRY,
    "SWIFT_THUMBNAIL_RECENCY_AGE_SECONDS": 86400,
    "SWIFT_THUMBNAIL_EXPIRY_CONTAINERS": ["wikipedia-en-local-thumb.d3"],
}


def context(container="wikipedia-en-local-thumb.d3", original_age=60, **config):
    ctx = SimpleNamespace(config=Config(**config))

    if container is not None:
        ctx.wikimedia_thumbnail_container = container

    if original_age is not None:
        ctx.wikimedia_original_timestamp = time.time() - original_age

    return ctx


class TestSpeculativeExpiry:
    def test_recent_upload_in_an_experiment_container_expires(self):
        assert EXPIRY <= thumbnail_expiry(context(**EXPERIMENT)) <= EXPIRY + JITTER

    def test_old_upload_is_kept(self):
        # The original has been around for a week, its thumbnails are worth
        # keeping.
        assert thumbnail_expiry(context(original_age=7 * 86400, **EXPERIMENT)) is None

    def test_container_outside_the_experiment_is_kept(self):
        assert thumbnail_expiry(context(container="wikipedia-de-local-thumb.a1", **EXPERIMENT)) is None

    def test_containers_are_matched_by_their_full_name(self):
        # Shards are listed individually, so the unsharded name is not in the
        # experiment.
        assert thumbnail_expiry(context(container="wikipedia-en-local-thumb", **EXPERIMENT)) is None

    def test_missing_container_is_kept(self):
        assert thumbnail_expiry(context(container=None, **EXPERIMENT)) is None

    def test_unknown_original_age_is_kept(self):
        # The loader could not parse Swift's x-timestamp, so we have no idea
        # how old the original is and leave the thumbnail alone.
        assert thumbnail_expiry(context(original_age=None, **EXPERIMENT)) is None

    def test_empty_container_list_turns_the_experiment_off(self):
        config = dict(EXPERIMENT, SWIFT_THUMBNAIL_EXPIRY_CONTAINERS=[])

        assert thumbnail_expiry(context(**config)) is None

    def test_zero_age_threshold_turns_the_experiment_off(self):
        config = dict(EXPERIMENT, SWIFT_THUMBNAIL_RECENCY_AGE_SECONDS=0)

        assert thumbnail_expiry(context(**config)) is None

    def test_zero_expiry_turns_everything_off(self):
        config = dict(EXPERIMENT, SWIFT_THUMBNAIL_EXPIRY_SECONDS=0)

        assert thumbnail_expiry(context(**config)) is None

    def test_unconfigured_means_no_expiry(self):
        assert thumbnail_expiry(context()) is None

    def test_jitter_stays_within_its_bounds(self):
        values = {thumbnail_expiry(context(**EXPERIMENT)) for _ in range(100)}

        assert all(EXPIRY <= value <= EXPIRY + JITTER for value in values)
        # Whole seconds, since that is what X-Delete-After takes.
        assert all(isinstance(value, int) for value in values)
        # A single value would mean the jitter isn't actually jittering.
        assert len(values) > 1
