#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# DjVu engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/vnd.djvu',
    '.djvu',
    lambda buffer: buffer[4:8] == b'FORM' and buffer[12:16] in (b'DJVU', b'DJVM', b'PM44', b'BM44')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.prepare_source(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        command = [
            self.context.config.DDJVU_PATH,
            '-format=ppm',
            '-page=%d' % page,
            self.source,
            '-'
        ]

        ppm = self.command(command)

        return super(Engine, self).create_image(ppm)
