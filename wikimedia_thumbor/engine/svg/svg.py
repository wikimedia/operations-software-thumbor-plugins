#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# SVG engine

import codecs
import os
import re
import tempfile

from wikimedia_thumbor.engine import BaseWikimediaEngine, CommandError
from wikimedia_thumbor.shell_runner import ShellRunner

BaseWikimediaEngine.add_format(
    'image/svg+xml',
    '.svg',
    lambda buffer: Engine.is_svg(buffer)
)


class Engine(BaseWikimediaEngine):
    @classmethod
    def is_svg(cls, buffer):
        # Quite wide, but it's better to let rsvg give a file a shot
        # rather than bail without trying
        # T186500 There can be an optional UTF-8 BOM at the beginning
        # T187088 The namespace might not be in the excerpt
        try:
            decoded_text = buffer[:10].decode('utf-8')
        except UnicodeDecodeError:
            return False

        return re.match(r'^(' + codecs.BOM_UTF8.decode('utf-8') + r')?<(\?xml|svg)', decoded_text)

    def create_image(self, buffer):
        self.prepare_source(buffer)

        tmp_handle, tmp_name = tempfile.mkstemp()
        # tempfile opens the file on create
        os.close(tmp_handle)

        command = [
            self.context.config.RSVG_CONVERT_PATH,
            self.source,
            '-u',
            '-f',
            'png',
            '-o',
            tmp_name
        ]

        if self.context.request.width > 0:
            command += ['-w', '%d' % self.context.request.width]

        if self.context.request.height > 0:  # pragma: no cover
            command += ['-h', '%d' % self.context.request.height]

        env = None
        if hasattr(self.context.request, 'lang'):
            env = {'LANG': self.context.request.lang.upper()}

        try:
            self.command(command, env)
        except CommandError as e:
            ShellRunner.rm_f(tmp_name)
            raise e

        with open(tmp_name, 'rb') as tmpfile:
            png = tmpfile.read()
        ShellRunner.rm_f(tmp_name)

        return super(Engine, self).create_image(png)

    # Disable this method in BaseEngine, do the conversion in create_image
    # instead
    def convert_svg_to_png(self, buffer):
        return buffer
