#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# ImageMagick engine

import subprocess
import wand.image as image
from wand.api import library, ctypes

from thumbor.utils import logger
from thumbor.engines import BaseEngine

from wikimedia_thumbor.shell_runner import ShellRunner

image.OPTIONS = frozenset(
    ['fill', 'jpeg:sampling-factor', 'pdf:use-cropbox', 'jpeg:size']
)

# wand doesn't support reading pixel blobs out of the box,
# only file blobs, so we have to monkey-patch that in

library.MagickConstituteImage.argtypes = [
    ctypes.c_void_p,
    ctypes.c_size_t,
    ctypes.c_size_t,
    ctypes.c_char_p,
    ctypes.c_uint,
    ctypes.c_void_p
]

ALPHA_TYPES = [
    'grayscalematte',
    'palettematte',
    'truecolormatte'
]


def read_blob(self, blob, format, width, height):
    r = library.MagickConstituteImage(
        self.wand,
        int(width),
        int(height),
        format.upper(),
        int(1),
        blob
    )

    if not r:
        self.raise_exception()

image.Image.read_blob = read_blob


class Engine(BaseEngine):
    def should_run(self, extension, buffer):
        return extension in ('.jpg', '.png')

    def create_image(self, buffer):
        im = image.Image()

        # If some resizing is going to happen, we need to lazy-load
        # the image later in resize() in order to be able to apply
        # jpeg:size
        if self.extension == '.jpg' and (
            self.context.request.width > 0 or
            self.context.request.height > 0
        ):
            self.buffer = buffer
        else:
            logger.debug('[IM] jpeg:size not required')
            im.read(blob=buffer)

        return im

    def read(self, extension=None, quality=None):
        # Sometimes Thumbor needs to read() the original as-is
        if hasattr(self, 'buffer'):
            return self.buffer

        return self.image.make_blob(format=extension.lstrip('.'))

    def crop(self, crop_left, crop_top, crop_right, crop_bottom):
        # Sometimes thumbor's resize algorithm will try to pre-crop
        # the image. However that gets in the way of the jpeg:size
        # optimization. I presume Thumbor does that to reduce interpolation
        # but it does so at the expense of cutting off one edge of the image
        if not hasattr(self, 'buffer'):
            self.image.crop(
                left=int(crop_left),
                top=int(crop_top),
                right=int(crop_right),
                bottom=int(crop_bottom)
            )

    def resize(self, width, height):
        if hasattr(self, 'buffer'):
            logger.debug('[IM] jpeg:size read')
            self.image.options['jpeg:size'] = '%dx%d' % (
                width,
                height
            )
            self.image.read(blob=self.buffer)
            # No override of size() needed anymore
            del self.buffer

            # Run reorientate again, as it might have be blocked
            # earlier because the image wasn't there
            if self.context.config.RESPECT_ORIENTATION:
                self.reorientate()

        self.image.resize(width=int(width), height=int(height))

    def flip_horizontally(self):
        self.image.flop()

    def flip_vertically(self):
        self.image.flip()

    def rotate(self, degrees):
        self.image.rotate(degree=degrees)

    def reorientate(self):
        # We can't reorientate right now because we have no image
        if hasattr(self, 'buffer'):
            return

        self.image.auto_orient()

    def image_data_as_rgb(self, update_image=True):
        converted = self.image.convert(self.mode)

        if update_image:
            self.image = converted

        return self.mode, converted.make_blob()

    def set_image_data(self, data):
        width, height = self.image.size

        rgb = image.Image()
        rgb.read_blob(
            blob=data,
            format=self.mode,
            width=width,
            height=height
        )

        self.image = rgb.convert(self.extension.lstrip('.'))

    @property
    def mode(self):
        if self.image.type in ALPHA_TYPES:
            return 'RGBA'

        return 'RGB'

    @property
    def size(self):
        if not hasattr(self, 'buffer'):
            return self.image.size

        # The size might be requested several times
        # while the image hasn't been read yet, we cache
        # that value for those situations
        if hasattr(self, 'saved_size'):
            return self.saved_size

        # In order to make use of jpeg:size, we need to
        # know the aspect ratio of the image without
        # ImageMagick reading the whole file (jpeg:size
        # has to be set *before* reading the file contents)
        command = ShellRunner.wrap_command([
            self.context.config.EXIFTOOL_PATH,
            '-s',
            '-s',
            '-s',
            '-ImageSize',
            '-'
        ], self.context)

        p = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stdin=subprocess.PIPE
        )
        p.stdin.write(self.buffer)
        stdout, stderr = p.communicate()

        size = stdout.rstrip().split('x')
        self.saved_size = [int(dimension) for dimension in size]

        return self.saved_size
