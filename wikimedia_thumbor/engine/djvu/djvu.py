#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# DjVu engine

from wikimedia_thumbor.engine.tiff import Engine as TiffEngine


TiffEngine.add_format(
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


class Engine(TiffEngine):
    def should_run(self, extension, buffer):
        return extension == '.djvu'

    def create_image(self, buffer):
        self.djvu_buffer = buffer
        self.prepare_temp_files(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        command = [
            self.context.config.DDJVU_PATH,
            '-format=tiff',
            '-page=%d' % page,
            self.source.name,
            self.destination.name
        ]

        tiff = self.exec_command(command)
        self.extension = '.tiff'

        # TiffEngine reads page a well, but by that point
        # there's only one page left
        self.context.request.page = 1

        # Pass the TIFF to TiffEngine
        return super(Engine, self).create_image(tiff)

    def read(self, extension=None, quality=None):
        if extension == '.djvu' and quality is None:
            # We're saving the source, let's save the DJVU
            return self.djvu_buffer

        # Beyond this point we're saving the JPG result
        if extension == '.djvu':
            extension = '.jpg'

        return super(Engine, self).read(extension, quality)
