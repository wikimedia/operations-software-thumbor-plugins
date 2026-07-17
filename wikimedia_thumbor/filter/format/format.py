#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Simply passes the format parameter
# This is a fork of thumbor's format parameter, running in the PRE_LOAD phase

from thumbor.filters import BaseFilter, filter_method, PHASE_PRE_LOAD
from thumbor.utils import logger
from tornado.web import HTTPError
from pathlib import PurePosixPath
from urllib.parse import urlparse

ALLOWED_FORMATS = ['jpg', 'jpeg', 'jpe', 'gif', 'png', 'webp']

ALLOWED_CONVERSIONS = {
    'jpg': {'jpg', 'webp'},
    'pdf': {'png', 'jpg', 'webp'},
    'svg': {'png', 'jpg', 'webp'},
    'png': {'png', 'webp'},
    'gif': {'gif', 'png', 'webp'},
    'webp': {'webp', 'png'},
}


class Filter(BaseFilter):
    phase = PHASE_PRE_LOAD

    @filter_method(BaseFilter.String)
    async def format(self, format):
        # Find and normalize the original file's extension.
        urlpath = urlparse(self.context.request.image_url).path
        format_in = PurePosixPath(urlpath).suffix.lower().lstrip(".")
        if format_in == 'jpeg':
            format_in = 'jpg'
        # Normalise the requested format.
        format_out = format.lower()
        if format_out in ('jpe', 'jpeg'):
            format_out = 'jpg'

        # Deny access to any non-allowed conversions (but allow any for formats missing from the above matrix).
        allowed_conversions = self.context.config.get('ALLOWED_CONVERSIONS', ALLOWED_CONVERSIONS)
        allowed = allowed_conversions.get(format_in)
        if allowed is not None and format_out not in allowed:
            raise HTTPError(400, f"Conversion from {format_in} to {format_out} is not allowed (permitted: " + ", ".join(allowed) + ")")

        if format.lower() not in ALLOWED_FORMATS:
            logger.debug('Format not allowed: %s' % format.lower())
            self.context.request.format = None
        else:
            logger.debug('Format specified: %s' % format.lower())
            self.context.request.format = format.lower()
