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
from tempfile import NamedTemporaryFile

from thumbor.loaders import LoaderResult
from thumbor.utils import logger

from tornado.process import Subprocess


from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.logging import log_extra
from wikimedia_thumbor.loader.swift import swift


swiftconn = None
swiftconn_private = None


def should_run(url):  # pragma: no cover
    normalized_url = _normalize_url(url).lower()

    if (normalized_url.endswith('.ogv') or
            normalized_url.endswith('.ogg') or
            normalized_url.endswith('.webm') or
            normalized_url.endswith('.mpg') or
            normalized_url.endswith('.mpeg')):
        return True

    return False


async def load(context, url):
    # Disable storage of original. These lines are useful if
    # you want your Thumbor instance to store all originals persistently
    # except video frames.
    #
    # from thumbor.storages.no_storage import Storage as NoStorage
    # context.modules.storage = NoStorage(context)

    normalized_url = _normalize_url(url)

    command = [
        context.config.FFPROBE_PATH,
        '-v',
        'error',
        '-show_entries',
        'format=duration',
        '-of',
        'default=noprint_wrappers=1:nokey=1'
    ]

    if hasattr(context.config, 'SWIFT_HOST'):
        command += [
            '-headers',
            'X-Auth-Token: %s' % get_swift_token(context),
        ]

    command += ['%s' % normalized_url]

    command = ShellRunner.wrap_command(command, context)

    logger.debug('[Video] load: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    status = await process.wait_for_exit(False)

    return await _parse_time_status(context, normalized_url, process, status)


def get_swift_token(context):
    url, token = swift(context).get_auth()
    return token


def _http_code_from_stderr(context, process, result, normalized_url):
    result.successful = False

    stderr = bytearray(4096)
    process.stderr.read_from_fd(stderr)

    extra = log_extra(context)
    extra['stderr'] = stderr
    extra['normalized_url'] = normalized_url

    logger.error(f'[Video] Fprobe/ffmpeg errored: {stderr}', extra=extra)
    http_error_re = re.compile(r'.*Server returned (\d\d\d).*', re.MULTILINE)
    code = None
    for stderr_line in stderr.decode('utf-8').split("\n"):
        logger.error("got code")
        code_match = http_error_re.match(stderr_line)
        if code_match:
            code = code_match

    if code:
        code = int(code.group(1))

    if code == 404:
        result.error = LoaderResult.ERROR_NOT_FOUND
    elif code == 599:
        result.error = LoaderResult.ERROR_TIMEOUT
    elif code == 500:
        result.error = LoaderResult.ERROR_UPSTREAM


async def _parse_time_status(context, normalized_url, process, status):
    if status != 0:
        result = LoaderResult()

        _http_code_from_stderr(context, process, result, normalized_url)
        process.stdout.close()
        process.stderr.close()

        return result
    else:
        output = await process.stdout.read_until_close()

        process.stdout.close()
        process.stderr.close()

        return await _parse_time(context, normalized_url, output)


async def _parse_time(context, normalized_url, output):
    # T183907 Some files have completely corrupt duration fields,
    # but we can still extract their first frame for a thumbnail
    try:
        duration = float(output)
    except ValueError:
        duration = 0

    try:
        seek = int(context.request.page)
    except AttributeError:
        seek = duration / 2

    return await seek_and_screenshot(context, normalized_url, seek)


async def seek_and_screenshot(context, normalized_url, seek):
    output_file = NamedTemporaryFile(delete=False)

    command = [
        context.config.FFMPEG_PATH,
        # Order is important, for fast seeking -ss and -headers have to be before -i
        # As explained on https://trac.ffmpeg.org/wiki/Seeking
        '-ss',
        '%d' % seek
    ]

    if hasattr(context.config, 'SWIFT_HOST'):
        command += [
            '-headers',
            'X-Auth-Token: %s' % get_swift_token(context)
        ]

    command += [
        '-i',
        '%s' % normalized_url,
        '-y',
        '-vframes',
        '1',
        '-an',
        '-f',
        'image2',
        '-vf',
        'scale=iw*sar:ih',  # T198043 apply any codec-specific aspect ratio
        '-nostats',
        '-loglevel',
        'fatal',
        output_file.name
    ]

    command = ShellRunner.wrap_command(command, context)

    logger.debug('[Video] _parse_time: %r' % command)

    process = Subprocess(
        command,
        stdout=Subprocess.STREAM,
        stderr=Subprocess.STREAM
    )

    status = await process.wait_for_exit(False)

    return await _process_done(process, context, normalized_url, seek, output_file, status)


async def _process_done(
        process,
        context,
        normalized_url,
        seek,
        output_file,
        status
        ):
    # T183907 Sometimes ffmpeg returns status 0 and actually fails to
    # generate a thumbnail. We double-check the existence of the thumbnail
    # in case of apparent success
    if status == 0:
        if os.stat(output_file.name).st_size == 0:
            status = -1

    # If rendering the desired frame fails, attempt to render the
    # first frame instead
    if status != 0 and seek > 0:
        return await seek_and_screenshot(context, normalized_url, 0)

    result = LoaderResult()

    if status != 0:  # pragma: no cover
        _http_code_from_stderr(context, process, result, normalized_url)
    else:
        result.successful = True
        result.buffer = output_file.read()

    process.stdout.close()
    process.stderr.close()

    output_file.close()

    try:
        os.unlink(output_file.name)
    except OSError as e:  # pragma: no cover
        if e.errno != errno.ENOENT:
            logger.error('[Video] Unable to unlink output file', extra=log_extra(context))
            raise

    return result


def _normalize_url(url):
    # URLs provided by Thumbor to load() are fully URL-escaped, including the protocol.
    # We unescape just the colon of the protocol to get a valid and properly escaped URL.
    rewritten_parts = []
    parts = url.split('/')

    for part in parts[:-1]:
        rewritten_parts.append(re.sub(r'%3A', r':', part))

    rewritten_parts.append(parts[-1])

    return '/'.join(rewritten_parts)
