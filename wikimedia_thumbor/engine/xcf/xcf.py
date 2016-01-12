#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# XCF engine

from wikimedia_thumbor_base_engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'image/xcf',
    '.xcf',
    lambda buffer: buffer.startswith('gimp xcf')
)


class Engine(BaseWikimediaEngine):
    def should_run(self, extension, buffer):
        return extension == '.xcf'

    def create_image(self, buffer):
        self.xcf_buffer = buffer
        self.prepare_temp_files(buffer)

        command = [
            self.context.config.XCF2PNG_PATH,
            self.source.name,
            '-o',
            self.destination.name
        ]

        png = self.exec_command(command)
        self.extension = '.png'

        return super(Engine, self).create_image(png)

    def read(self, extension=None, quality=None):
        if extension == '.xcf' and quality is None:
            # We're saving the source, let's save the XCF
            return self.xcf_buffer

        # Beyond this point we're saving the PNG result
        if extension == '.xcf':
            extension = '.png'

        return super(Engine, self).read(extension, quality)
