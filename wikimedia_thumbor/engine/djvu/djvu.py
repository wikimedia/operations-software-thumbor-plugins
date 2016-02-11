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
    lambda buffer: buffer.startswith('FORM', 4, 8) and
    (
        buffer.startswith('DJVU', 12, 16) or
        buffer.startswith('DJVM', 12, 16) or
        buffer.startswith('PM44', 12, 16) or
        buffer.startswith('BM44', 12, 16)
    )
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.prepare_temp_files(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        command = [
            self.context.config.DDJVU_PATH,
            '-format=pbm',
            '-page=%d' % page,
            self.source.name,
            self.destination.name
        ]

        pbm = self.exec_command(command)

        # Pass the PBM to the base engine and in turn to the
        # imagemagick engine
        im = super(Engine, self).create_image(pbm)
        # ddjvu seems to have a bug where it sets a depth of 1
        # when the DjVu is grayscale, making the image interpreted
        # as bilevel by wand when it shouldn't be
        im.depth = 8

        return im
