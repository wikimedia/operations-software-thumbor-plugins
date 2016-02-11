#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Video engine

from wikimedia_thumbor.engine import BaseWikimediaEngine


BaseWikimediaEngine.add_format(
    'video/ogg',
    '.ogv',
    lambda buffer: buffer.startswith('OggS')
)

BaseWikimediaEngine.add_format(
    'video/webm',
    '.webm',
    lambda buffer: buffer.startswith('\x1aE\xdf\xa3')
)


class Engine(BaseWikimediaEngine):
    def create_image(self, buffer):
        self.original_buffer = buffer
        self.prepare_temp_files(buffer)

        command = [
            self.context.config.FFPROBE_PATH,
            '-v',
            'error',
            '-show_entries',
            'format=duration',
            '-of',
            'default=noprint_wrappers=1:nokey=1',
            self.source.name
        ]

        duration = float(self.command(command))

        try:
            seek = self.context.request.page
        except (AttributeError, EOFError):
            seek = duration / 2

        command = [
            self.context.config.FFMPEG_PATH,
            # Order is important, for fast seeking -ss has to come before -i
            # As explained on https://trac.ffmpeg.org/wiki/Seeking
            '-ss',
            '%d' % seek,
            '-i',
            self.source.name,
            '-y',
            '-vframes',
            '1',
            '-an',
            '-f',
            'image2',
            '-nostats',
            '-loglevel',
            'error',
            self.destination.name
        ]

        jpg = self.exec_command(command)

        return super(Engine, self).create_image(jpg)
