#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Ghostscript engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'application/pdf',
    '.pdf',
    lambda buffer: buffer.startswith('%PDF')
)


class Engine(BaseWikimediaEngine):
    def should_run(self, extension, buffer):
        return extension == '.pdf'

    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_temp_files(buffer)

        try:
            page = self.context.request.page
        except AttributeError:
            page = 1

        command = [
            self.context.config.GHOSTSCRIPT_PATH,
            "-sDEVICE=tiff24nc",
            "-sOutputFile=%s" % self.destination.name,
            "-dFirstPage=%d" % page,
            "-dLastPage=%d" % page,
            "-r150",
            "-dBATCH",
            "-dNOPAUSE",
            "-q",
            "-f%s" % self.source.name
        ]

        tiff = self.exec_command(command)

        return super(Engine, self).create_image(tiff)
