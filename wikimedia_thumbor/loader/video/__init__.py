#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2016 Wikimedia Foundation

# Video loader, only loads the frame needed from a remote video
# Do not use it as-is with persistent storage of originals,
# otherwise the first frame requested will be stored as the
# original for subsequent requests

import errno
import re
import os
from functools import partial
from tempfile import NamedTemporaryFile
from urllib import unquote

from thumbor.loaders import LoaderResult
from thumbor.utils import logger

from tornado.concurrent import return_future
from tornado.process import Subprocess
import tornado.simple_httpclient


from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.loader import are_request_dimensions_valid


def should_run(url):  # pragma: no cover
    unquoted_url = unquote(url).lower()

    if (unquoted_url.endswith('.ogv') or
            unquoted_url.endswith('.ogg') or
            unquoted_url.endswith('.webm')):
        return True

    return False


@return_future
def load(context, url, callback):
    return load_sync(context, url, callback)


def load_sync(context, url, callback):
    unquoted_url = unquote(url)

    # First we do a HEAD request to look at the X-Content-Dimensions header,
    # if there is any. This allows us to stop the request very early if the
    # client asks for a thumbnail width we won't render (equal or greater than
    # the original's width).

    client = tornado.simple_httpclient.SimpleAsyncHTTPClient(
        max_clients=context.config.HTTP_LOADER_MAX_CLIENTS,
        max_body_size=context.config.HTTP_LOADER_MAX_BODY_SIZE
    )

    user_agent = None
    if context.config.HTTP_LOADER_FORWARD_USER_AGENT:
        if 'User-Agent' in context.request_handler.request.headers:
            user_agent = context.request_handler.request.headers['User-Agent']
    if user_agent is None:
        user_agent = context.config.HTTP_LOADER_DEFAULT_USER_AGENT

    req = tornado.httpclient.HTTPRequest(
        url=unquoted_url,
        connect_timeout=context.config.HTTP_LOADER_CONNECT_TIMEOUT,
        request_timeout=context.config.HTTP_LOADER_REQUEST_TIMEOUT,
        follow_redirects=context.config.HTTP_LOADER_FOLLOW_REDIRECTS,
        max_redirects=context.config.HTTP_LOADER_MAX_REDIRECTS,
        user_agent=user_agent,
        proxy_host=encode(context.config.HTTP_LOADER_PROXY_HOST),
        proxy_port=context.config.HTTP_LOADER_PROXY_PORT,
        proxy_username=encode(context.config.HTTP_LOADER_PROXY_USERNAME),
        proxy_password=encode(context.config.HTTP_LOADER_PROXY_PASSWORD),
        ca_certs=encode(context.config.HTTP_LOADER_CA_CERTS),
        client_key=encode(context.config.HTTP_LOADER_CLIENT_KEY),
        client_cert=encode(context.config.HTTP_LOADER_CLIENT_CERT),
        method='HEAD'
    )

    client.fetch(
        req, callback=partial(
            process_headers_and_maybe_continue,
            unquoted_url=unquoted_url,
            callback=callback,
            context=context
        )
    )


def process_headers_and_maybe_continue(response, unquoted_url, callback, context):
    '''
    Checks the X-Content-Dimensions header and continues if the request is invalid
    or the header is absent/errorneous.
    '''
    headers = response.headers.get_list('X-Content-Dimensions')

    if len(headers):
        content_dimensions_header = headers.pop()
        if not are_request_dimensions_valid(context, content_dimensions_header):
            # This will result in a 400 and the request won't proceed further
            result = LoaderResult()
            result.successful = False
            result.error = 400
            log_extra = {'url': context.request.url}
            logger.error('[SWIFT_LOADER] dimensions check failed: %s' % unquoted_url, extra=log_extra)
            context.metrics.incr('video_loader.status.dimensions_error')
            callback(result)
            return

    # No Dimensions error, we proceed to using ffprobe to determine the length of the video.
    # This is necessary because by default we want the thumbnail to be the midpoint
    # of the video, and when extracting an image ffmpeg needs to be given a specific
    # time.

    command = ShellRunner.wrap_command([
        context.config.FFPROBE_PATH,
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1',
        '%s' % unquoted_url
    ], context)

    logger.debug('[Video] ffprobe: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    process.set_exit_callback(
        partial(
            process_ffprobe_status_and_maybe_continue,
            context,
            unquoted_url,
            callback,
            process
        )
    )


def process_ffprobe_status_and_maybe_continue(context, url, callback, process, status):
    '''
    Checks the exit status from ffprobe. If ffprobe errors, the request fails.
    If it succeeds, we then read the output.
    '''
    if status != 0:
        context.metrics.incr('video_loader.status.ffprobe_error')
        result = LoaderResult()

        http_code_from_stderr(context, process, result)
        process.stdout.close()
        process.stderr.close()

        callback(result)
    else:
        process.stdout.read_until_close(
            partial(
                process_time_and_maybe_continue,
                context,
                url,
                callback
            )
        )

        process.stdout.close()
        process.stderr.close()


def process_time_and_maybe_continue(context, url, callback, output):
    '''
    Reads the duration from the ffprobe output and either use the midpoint
    or override with the page parameter if the client requested a specific
    point in time. Proceed to seek in the video and extract a screenshot.

    TODO: bypass ffprobe altogether when page is specified
    '''
    duration = float(output)
    unquoted_url = unquote(url)

    try:
        seek = int(context.request.page)
    except AttributeError:
        seek = duration / 2

    seek_and_screenshot(callback, context, unquoted_url, seek)


def seek_and_screenshot(callback, context, unquoted_url, seek):
    '''
    Uses ffmpeg to seek a specific point in the video and extract
    the screenshot from it.
    '''
    output_file = NamedTemporaryFile(delete=False)

    command = ShellRunner.wrap_command([
        context.config.FFMPEG_PATH,
        # Order is important, for fast seeking -ss has to come before -i
        # As explained on https://trac.ffmpeg.org/wiki/Seeking
        '-ss',
        '%d' % seek,
        '-i',
        '%s' % unquoted_url,
        '-y',
        '-vframes',
        '1',
        '-an',
        '-f',
        'image2',
        '-nostats',
        '-loglevel',
        'fatal',
        output_file.name
    ], context)

    logger.debug('[Video] _parse_time: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    process.set_exit_callback(
        partial(
            callback_with_screenshot,
            callback,
            process,
            context,
            unquoted_url,
            seek,
            output_file
        )
    )


def callback_with_screenshot(
        callback,
        process,
        context,
        unquoted_url,
        seek,
        output_file,
        status
        ):
    '''
    Reads the status from ffmpeg. If it fails, attempt to render the first frame.
    If it succeeds, return the screenshot.
    '''

    # If rendering the desired frame fails, attempt to render the
    # first frame instead
    if status != 0 and seek > 0:
        seek_and_screenshot(callback, context, unquoted_url, 0)
        return

    result = LoaderResult()

    if status != 0:  # pragma: no cover
        context.metrics.incr('video_loader.status.screenshot_error')
        http_code_from_stderr(context, process, result)
    else:
        context.metrics.incr('video_loader.status.success')
        result.successful = True
        result.buffer = output_file.read()

    process.stdout.close()
    process.stderr.close()

    output_file.close()

    try:
        os.unlink(output_file.name)
    except OSError as e:  # pragma: no cover
        if e.errno != errno.ENOENT:
            raise

    callback(result)


def http_code_from_stderr(context, process, result):
    '''
    Converts a command failure from ffprobe or ffmpeg into
    an HTTP error code for the response.
    '''
    result.successful = False
    stderr = process.stderr.read_from_fd()

    logger.warning('[Video] Fprobe/ffmpeg errored: %r' % stderr)
    code = re.match('.*Server returned (\d\d\d).*', stderr)

    if code:
        code = int(code.group(1))

    if code == 404:
        context.metrics.incr('video_loader.status.not_found')
        result.error = LoaderResult.ERROR_NOT_FOUND
    elif code == 599:
        context.metrics.incr('video_loader.status.timeout')
        result.error = LoaderResult.ERROR_TIMEOUT
    elif code == 500:
        context.metrics.incr('video_loader.status.upstream_error')
        result.error = LoaderResult.ERROR_UPSTREAM


def encode(string):
    return None if string is None else string.encode('ascii')
