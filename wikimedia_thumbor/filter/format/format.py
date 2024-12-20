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


ALLOWED_FORMATS = ['png', 'jpeg', 'jpg', 'gif', 'webp']


class Filter(BaseFilter):
    phase = PHASE_PRE_LOAD

    @filter_method(BaseFilter.String)
    async def format(self, format):
        if format.lower() not in ALLOWED_FORMATS:
            logger.debug('Format not allowed: %s' % format.lower())
            self.context.request.format = None
        else:
            logger.debug('Format specified: %s' % format.lower())
            self.context.request.format = format.lower()
