import math
from importlib.metadata import PackageNotFoundError, version


def _distribution_version(name):
    try:
        return version(name)
    except PackageNotFoundError:
        return None


# Looked up once at import time: log_extra() runs on every single debug log
# line, and resolving distribution metadata hits the filesystem.
THUMBOR_VERSION = _distribution_version('thumbor')
WIKIMEDIA_THUMBOR_VERSION = _distribution_version('wikimedia_thumbor')


def record_timing(context, duration, statsd_key, header_name=None):
    # In order to copy Python 2 behaviour of round() method, namely "round
    # half away from zero" rounding, method math.floor() and adding 0.5 to
    # the value which will be rounded are used.
    duration = math.floor((duration.total_seconds() * 1000) + 0.5)

    context.metrics.timing(
        statsd_key,
        duration
    )

    if header_name is not None:
        context.request_handler.add_header(
            header_name,
            duration
        )


def log_extra(context):
    try:
        url = context.request.url
    except AttributeError:
        url = None

    try:
        request_id = context.request_handler.request.headers.get('Thumbor-Request-Id', 'None')
    except AttributeError:
        request_id = None

    extras = {
        'url': url,
        'thumbor-request-id': request_id,
        'thumbor-version': THUMBOR_VERSION,
        'wikimedia-thumbor-version': WIKIMEDIA_THUMBOR_VERSION
    }
    return extras
