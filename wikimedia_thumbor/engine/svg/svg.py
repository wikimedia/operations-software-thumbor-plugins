#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# SVG engine

from bs4 import BeautifulSoup

from wikimedia_thumbor.engine import BaseWikimediaEngine

BaseWikimediaEngine.add_format(
    'image/svg+xml',
    '.svg',
    lambda buffer: Engine.is_svg(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_svg(cls, buffer):
        soup = BeautifulSoup(buffer, 'xml')

        return soup.svg is not None

    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_temp_files(buffer)

        command = [
            self.context.config.RSVG_CONVERT_PATH,
            self.source.name,
            '-f',
            'png',
            '-o',
            self.destination.name
        ]

        if self.context.request.width > 0:
            command += ['-w', '%d' % self.context.request.width]

        if self.context.request.height > 0:
            command += ['-h', '%d' % self.context.request.height]

        png = self.exec_command(command)

        return super(Engine, self).create_image(png)
