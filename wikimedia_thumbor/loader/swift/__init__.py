#!/usr/bin/python

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Swift loader. Streams objects from Swift with auth

import datetime
from functools import partial
from tempfile import NamedTemporaryFile

import requests
import tornado.simple_httpclient
from swiftclient import client
from swiftclient.exceptions import ClientException
from thumbor.loaders import LoaderResult
from thumbor.utils import logger

from wikimedia_thumbor.logging import log_extra, record_timing
from wikimedia_thumbor.shell_runner import ShellRunner

# Originals are streamed from Swift in chunks of this size, rather than being
# read into memory in one go.
SWIFT_CHUNK_SIZE = 16 * 1024 * 1024


def should_run(url):  # pragma: no cover
    return True


def cleanup_temp_file(context, path):
    logger.debug(f"[SWIFT_LOADER] cleanup_temp_file: {path}", extra=log_extra(context))
    ShellRunner.rm_f(path)


def swift(context):
    authurl = context.config.SWIFT_HOST + context.config.SWIFT_AUTH_PATH

    # This allows us to set the value via config, instead of depending on the
    # x-storage-url header returned by Swift during auth. This is a requirement
    # for communicating with Swift via HTTPS.
    os_options = {"object_storage_url": context.config.SWIFT_HOST + context.config.SWIFT_API_PATH}

    conn = client.Connection(
        user=context.config.SWIFT_PRIVATE_USER if context.private else context.config.SWIFT_USER,
        key=context.config.SWIFT_PRIVATE_KEY if context.private else context.config.SWIFT_KEY,
        authurl=authurl,
        timeout=context.config.SWIFT_CONNECTION_TIMEOUT,
        retries=context.config.SWIFT_RETRIES,
        cacert=context.config.HTTP_LOADER_CA_CERTS,
        os_options=os_options,
    )

    return conn


def fetch_to_temp_file(context, container, path, excerpt_length):
    """Stream an object from Swift into a temp file, chunk by chunk.

    Returns the object headers, the (closed) temp file, the first
    excerpt_length bytes of the object and its total size."""
    headers, chunks = swift(context).get_object(container, path, resp_chunk_size=SWIFT_CHUNK_SIZE)

    f = NamedTemporaryFile(delete=False)
    excerpt = b""
    size = 0

    try:
        for chunk in chunks:
            if len(excerpt) < excerpt_length:
                excerpt += chunk[: excerpt_length - len(excerpt)]
            f.write(chunk)
            size += len(chunk)
    except BaseException:
        f.close()
        cleanup_temp_file(context, f.name)
        raise

    f.close()

    return headers, f, excerpt, size


async def load(context, url):
    logger.debug(f"[SWIFT_LOADER] load: {url}", extra=log_extra(context))

    result = LoaderResult()

    container = context.wikimedia_original_container
    path = context.wikimedia_original_filepath

    try:
        logger.debug(f"[SWIFT_LOADER] fetching {path} from container {container}", extra=log_extra(context))

        start = datetime.datetime.now()

        # logging.disable(logging.ERROR)
        excerpt_length = context.config.LOADER_EXCERPT_LENGTH

        headers, f, body, size = await tornado.ioloop.IOLoop.instance().run_in_executor(None, fetch_to_temp_file, context, container, path, excerpt_length)
        # logging.disable(logging.NOTSET)

        record_timing(context, datetime.datetime.now() - start, "swift.original.read.success", "Thumbor-Swift-Original-Success-Time")

        context.metrics.incr("swift_loader.status.success")

        try:
            context.wikimedia_original_timestamp = float(headers.get("x-timestamp"))
        except (AttributeError, TypeError, ValueError):
            context.wikimedia_original_timestamp = None

        logger.debug("[SWIFT_LOADER] wrote %d bytes to temp file" % size, extra=log_extra(context))

        # XXX hack: If the file is an STL, we overwrite the first five bytes
        # with the word "solid", to trick the MIME detection pipeline.
        extension = path[-4:].lower()
        isSTL = extension == ".stl"

        # See above - text STLs have this string here anyway, and
        # binary STLs ignore the first 80 bytes, so this string will
        # be ignored.
        if isSTL:
            body = b"solid" + body[5:]

        if len(body) == excerpt_length:
            logger.debug(f"[SWIFT_LOADER] return_contents: {f.name}", extra=log_extra(context))
            context.wikimedia_original_file = f

            tornado.ioloop.IOLoop.instance().call_later(context.config.HTTP_LOADER_TEMP_FILE_TIMEOUT, partial(cleanup_temp_file, context, context.wikimedia_original_file.name))
        else:
            logger.debug("[SWIFT_LOADER] return_contents: small body")
            cleanup_temp_file(context, f.name)

        result.buffer = body
    except ClientException as e:
        record_timing(context, datetime.datetime.now() - start, "swift.original.read.miss", "Thumbor-Swift-Original-Miss-Time")
        # logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_NOT_FOUND
        logger.error(f"[SWIFT_LOADER] get_object failed: {url} {e!r}", extra=log_extra(context))
        context.metrics.incr("swift_loader.status.client_exception")
    except requests.ConnectionError as e:
        record_timing(context, datetime.datetime.now() - start, "swift.original.read.exception", "Thumbor-Swift-Original-Exception-Time")
        # logging.disable(logging.NOTSET)
        result.successful = False
        result.error = LoaderResult.ERROR_UPSTREAM
        logger.error(f"[SWIFT_LOADER] get_object failed: {url} {e!r}", extra=log_extra(context))
        context.metrics.incr("swift_loader.status.connection_error")

    return result
