#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Simply passes the lang parameter

from thumbor.filters import BaseFilter, filter_method, PHASE_PRE_LOAD


class Filter(BaseFilter):
    phase = PHASE_PRE_LOAD

    @filter_method(BaseFilter.String)
    async def lang(self, value):
        self.context.request.lang = value
