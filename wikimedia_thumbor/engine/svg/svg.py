#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# SVG engine

from io import BytesIO
import xml.etree.cElementTree as cElementTree

from wikimedia_thumbor.engine import BaseWikimediaEngine

BaseWikimediaEngine.add_format(
    'image/svg+xml',
    '.svg',
    lambda buffer: Engine.is_svg(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_svg(cls, buffer):
        try:
            for event, element in cElementTree.iterparse(
                BytesIO(buffer), ('start',)
            ):
                return element.tag == '{http://www.w3.org/2000/svg}svg'
        except cElementTree.ParseError:
            pass

        return False

    def should_run(self, extension, buffer):
        return extension == '.svg'

    def create_image(self, buffer):
        self.svg_buffer = buffer
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
        self.extension = '.png'

        return super(Engine, self).create_image(png)

    def read(self, extension=None, quality=None):
        if extension == '.svg' and quality is None:
            # We're saving the source, let's save the SVG
            return self.svg_buffer

        # Beyond this point we're saving the PNG result
        if extension == '.svg':
            extension = '.png'

        return super(Engine, self).read(extension, quality)
