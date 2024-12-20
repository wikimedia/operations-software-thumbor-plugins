#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# ImageMagick engine

import json
import logging
from tempfile import NamedTemporaryFile
from pyexiv2 import ImageMetadata, ExifValueError

from thumbor.utils import logger
from thumbor.engines import BaseEngine

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.exiftool_runner import ExiftoolRunner
from wikimedia_thumbor.logging import log_extra
from decimal import Decimal, ROUND_HALF_DOWN


class ImageMagickException(Exception):
    pass


class Engine(BaseEngine):
    exiftool = ExiftoolRunner()

    @classmethod
    def add_format(cls, mime, ext, fn):
        # Unfortunately there is no elegant way to extend Thumbor to support
        # a new MIME type, which is why this monkey-patching is done here
        from thumbor.utils import EXTENSION
        EXTENSION[mime] = ext
        from thumbor.engines import BaseEngine
        old_get_mimetype = BaseEngine.get_mimetype

        @classmethod
        def new_get_mimetype(cls, buffer):
            if fn(buffer):
                return mime

            return old_get_mimetype(buffer)

        BaseEngine.get_mimetype = new_get_mimetype

    def create_image(self, buffer):
        # This should be enough for now, if memory blows up on huge files we
        # can could use an mmap here
        if hasattr(self.context, 'wikimedia_original_file'):
            self.debug('[IM] Grabbing filename from context')
            temp_file = self.context.wikimedia_original_file
        else:
            self.debug('[IM] Dumping buffer into temp file')
            temp_file = NamedTemporaryFile(delete=False)
            temp_file.write(buffer)
            temp_file.close()

        self.exif_dict = {}
        self.operators = []

        try:
            self.page = self.context.request.page - 1
        except AttributeError:
            self.page = 0

        # Read EXIF data from file first. This will get us the
        # size if we need it for the jpeg:size option, as well as the
        # ICC profile name in case we need to do profile swapping and
        # the various EXIF fields we want to keep
        self.read_exif(temp_file)

        return temp_file

    def jpeg_size(self):
        exif_image_size = self.exif_dict['ImageSize']
        buffer_size = exif_image_size.split('x')
        buffer_size = [float(x) for x in buffer_size]
        buffer_ratio = buffer_size[0] / buffer_size[1]

        if 'Pyexiv2Orientation' in self.exif_dict:
            if self.exif_dict['Pyexiv2Orientation'] in (6, 8):
                buffer_ratio = buffer_size[1] / buffer_size[0]

        # If the JPEG size hint is too close to the target size,
        # We can end up with rounding errors on the final output size,
        # with width being different than the requested width.
        # Therefore, we make the hint twice the target size

        width = self.context.request.width * 2
        height = self.context.request.height * 2

        if width == 0:
            width = Decimal(height * buffer_ratio).quantize(0, ROUND_HALF_DOWN)

        if height == 0:
            height = Decimal(width / buffer_ratio).quantize(0, ROUND_HALF_DOWN)

        jpeg_size = '%dx%d' % (width, height)
        self.debug('[IM] jpeg:size hint: %r' % jpeg_size)
        return jpeg_size

    def read_exif(self, input_temp_file):
        fields = [
            'ImageSize',
            'ProfileDescription',
            'ColorType',
            'FileType',
            'Transparency'
        ]

        fields += self.context.config.EXIF_FIELDS_TO_KEEP

        command = [
            '-j'
        ]

        command += ['-{0}'.format(i) for i in fields]

        # T172556 We read EXIF Orientation with pyexiv2 because exiftool is
        # unreliable for that field (overzealous in the way it interprets the field).
        # We can't replace all use of exiftool with pyexiv2 because ICC profile
        # support was only introduced in exiv2 0.26 (not available on Jessie yet)
        # and it can only extract the ICC profile, not get its name/description upfront.
        # Which would make the sRGB replacement more difficult (it's unclear how many
        # variations of the binary content for that family of profiles there are).

        metadata = ImageMetadata(input_temp_file.name)
        try:
            try:
                # T178072 pyexviv2 writes to stderr even if the exception is caught
                logging.disable(logging.ERROR)
                metadata.read()
            finally:
                logging.disable(logging.NOTSET)

            if 'Exif.Image.Orientation' in metadata.exif_keys:
                # Distinctive key name to avoid colliding with EXIF_FIELDS_TO_KEEP
                self.exif_dict['Pyexiv2Orientation'] = metadata.get('Exif.Image.Orientation').value
        except (IOError, ExifValueError, TypeError):
            self.debug('[IM] Could not read EXIF with pyexiv2')
        except RuntimeError as e:
            # T245440 exiv2 0.25-3.1+deb9u1 handles missing metadata as corruption, and
            # pyexiv2 raises that as a generic runtime error.
            if e.args[0] == 'corrupted image metadata':
                self.debug('[IM] Could not read EXIF with pyexiv2')
            else:
                raise

        stdout = Engine.exiftool.command(
            context=self.context,
            pre=command,
            input_temp_file=input_temp_file
        )

        # index at 0 because we're processing a single file
        self.exif_dict.update(json.loads(stdout.decode('utf-8'))[0])

        self.debug('[IM] EXIF: %r' % self.exif_dict)

        if 'ImageSize' in self.exif_dict:
            self.internal_size = [int(x) for x in self.exif_dict['ImageSize'].split('x')]
        else:
            # Have not been able to find a test file where that EXIF field comes up unpopulated
            self.internal_size = (1, 1)  # pragma: no cover

        # If we encounter any non-sRGB ICC profile, we save it to re-apply
        # it to the result

        if 'ProfileDescription' not in self.exif_dict:
            self.debug('[IM] File has no ICC profile')
            return

        expected_profile = self.context.config.EXIF_TINYRGB_ICC_REPLACE.lower()
        profile = self.exif_dict['ProfileDescription'].lower()

        if profile == expected_profile:
            self.icc_profile_path = self.context.config.EXIF_TINYRGB_PATH
            self.debug('[IM] File has sRGB profile')
            return

        self.debug('[IM] File has non-sRGB profile')

        command = [
            '-icc_profile',
            '-b',
        ]

        self.icc_profile_saved = Engine.exiftool.command(
            context=self.context,
            pre=command,
            input_temp_file=input_temp_file
        )

    def process_exif(self, buffer):
        self.debug('[IM] Processing EXIF')

        command = [
            '-all=',  # Strip all existing metadata
        ]

        # Create the temp file when we need it
        if hasattr(self, 'icc_profile_saved'):
            self.debug('[IM] Putting saved ICC profile into temp file')
            profile_file = NamedTemporaryFile(delete=False)
            profile_file.write(self.icc_profile_saved)
            profile_file.close()
            self.icc_profile_path = profile_file.name
            del self.icc_profile_saved

        # Copy the ICC profile
        if hasattr(self, 'icc_profile_path'):
            command += ['-icc_profile<=%s' % self.icc_profile_path]

        for field in self.context.config.EXIF_FIELDS_TO_KEEP:
            if field in self.exif_dict:
                value = self.exif_dict[field]
                command += ['-%s=%s' % (field, value)]

        postCommand = [
            '-o',
            '-'  # Write to stdout
        ]

        stdout = Engine.exiftool.command(
            pre=command,
            post=postCommand,
            context=self.context,
            buffer=buffer
        )

        tinyrgb_path = self.context.config.EXIF_TINYRGB_PATH

        # Clean up saved non-sRGB profile if needed
        if (hasattr(self, 'icc_profile_path')
                and self.icc_profile_path != tinyrgb_path):
            ShellRunner.rm_f(self.icc_profile_path)
            del self.icc_profile_path

        return stdout

    def process_read_parameters(self, extension, quality):
        extension = extension.lstrip('.')
        original_quality = quality

        if extension == 'webp':
            lossless = ('FileType' in self.exif_dict and self.exif_dict['FileType'] in ['SVG', 'PNG'])

            # We need to use a JPG as an intermediary for WebP conversion in order to
            # be able to apply the EXIF filtering
            if 'FileType' in self.exif_dict and self.exif_dict['FileType'] == 'JPEG':
                extension = 'jpg'
                quality = 100
            else:
                extension = 'png32'

            self.webp = {'quality': original_quality, 'lossless': lossless}
        else:
            self.webp = False

        # -quality in ImageMagick has a different meaning for PNG
        # See https://www.imagemagick.org/script/command-line-options.php#quality
        if extension.startswith('png'):
            quality = 95

        return extension, quality

    def read(self, extension=None, quality=None):
        self.debug('[IM] read: %s %d' % (extension, quality))

        extension, quality = self.process_read_parameters(extension, quality)

        config = self.context.config

        operators = [
            '-quality',
            '%d' % quality
        ]

        if hasattr(config, 'CHROMA_SUBSAMPLING') and config.CHROMA_SUBSAMPLING:
            cs = config.CHROMA_SUBSAMPLING
            self.debug('[IM] Chroma subsampling: %r' % cs)
            operators += [
                '-sampling-factor',
                cs
            ]

        self.debug('[IM] Generating image with quality %d' % quality)

        if extension == 'jpg' and self.context.config.PROGRESSIVE_JPEG:
            operators += [
                '-interlace',
                'Plane'
            ]

        self.queue_operators(operators)

        last_operators = [
            '%s[%d]' % (self.image.name, self.page),
            '%s:-' % extension,
        ]

        returncode, stderr, result = self.run_operators(last_operators)

        # If the requested page failed, try the cover
        if returncode != 0 and self.page > 0:
            self.page = 0
            last_operators = [
                '%s[%d]' % (self.image.name, self.page),
                '%s:-' % extension,
            ]
            returncode, stderr, result = self.run_operators(last_operators)

        if returncode != 0:
            ShellRunner.rm_f(self.image.name)  # pragma: no cover
            raise ImageMagickException('Failed to convert image %s' % stderr)  # pragma: no cover

        self.operators = []

        # Going forward, we're dealing with a single page document
        if self.page > 0:
            self.page = 0

        if extension == 'jpg':
            result = self.process_exif(result)

        if hasattr(self, 'webp') and self.webp:
            result = self.maybe_convert_to_webp(result)

        ShellRunner.rm_f(self.image.name)

        return result

    def crop(self, crop_left, crop_top, crop_right, crop_bottom):
        # Sometimes thumbor's resize algorithm will try to pre-crop
        # the image. We don't want that.
        pass

    def realcrop(self, crop_left, crop_top, crop_right, crop_bottom):
        self.debug(
            '[IM] crop: %r %r %r %r' % (
                crop_left,
                crop_top,
                crop_right,
                crop_bottom
            )
        )

        width = int(crop_right) - int(crop_left)
        height = int(crop_bottom) - int(crop_top)

        operators = [
            '-crop',
            '%dx%d+%d+%d' % (width, height, crop_left, crop_top)
        ]

        self.queue_operators(operators)

    def resize(self, width, height):
        self.debug('[IM] resize: %r %r' % (width, height))

        self.internal_size = (width, height)

        operators = []

        if self.extension == '.jpg':
            operators += [
                '-define',
                'jpeg:size=%s' % self.jpeg_size(),
            ]

        exif_image_size = self.exif_dict['ImageSize']
        buffer_size = exif_image_size.split('x')
        buffer_size = [float(x) for x in buffer_size]
        buffer_ratio = buffer_size[0] / buffer_size[1]

        if 'Pyexiv2Orientation' in self.exif_dict:
            if self.exif_dict['Pyexiv2Orientation'] in (6, 8):
                buffer_ratio = buffer_size[1] / buffer_size[0]

        # We have a slightly different calculation/rounding strategy than Thumbor
        # when it comes to calculate target width/height when only one dimension
        # is provided
        if self.context.request.height == 0 and self.context.request.width > 0:
            target_size = '%dx%d' % (int(width), Decimal(width / buffer_ratio).quantize(0, ROUND_HALF_DOWN))
        elif self.context.request.height > 0 and self.context.request.width == 0:
            target_size = '%dx%d' % (Decimal(height * buffer_ratio).quantize(0, ROUND_HALF_DOWN), int(height))
        else:
            target_size = '%dx%d' % (int(width), int(height))

        # The ^ + gravity + extent trick is necessary to ensure that we get a thumbnail
        # of exactly the width we've requested. In some edge cases a tiny fraction
        # of the image might be cropped out. This is unavoidable with ImageMagick
        # See http://www.imagemagick.org/Usage/resize/ for details

        operators += [
            '-resize',
            '%s^' % target_size,
            '-gravity',
            'center',
            '-extent',
            target_size
        ]

        # T198370 "-background none" is necessary to preserve transparency of PNG thumbnails
        # on the Debian Jessie version of IM (6.8.9-9). Only apply to RGBA and Palette (indexed)
        # PNGs, because otherwise it would turn thumbnails of RGB PNGs into RGBA, thumbnails
        # increasing their file size significantly.
        if ('ColorType' in self.exif_dict
            and self.exif_dict['ColorType'] in ['RGB with Alpha', 'Grayscale with Alpha', 'Palette']) \
                or 'Transparency' in self.exif_dict:
            operators += ['-background', 'none']

        self.queue_operators(operators)

    def flip_horizontally(self):
        self.debug('[IM] flip_horizontally')

        self.queue_operators(['-flop'])

    def flip_vertically(self):
        self.debug('[IM] flip_vertically')

        self.queue_operators(['-flip'])

    def rotate(self, degrees):
        self.debug('[IM] rotate: %r' % degrees)

        self.queue_operators(['-rotate', '%s' % degrees])

    def reorientate(self):
        self.debug('[IM] reorientate')

        # T173804 Avoid ImageMagick -auto-orient which is overzealous
        # in interpreting various EXIF fields instead of just Orientation

        if 'Pyexiv2Orientation' in self.exif_dict:
            if self.exif_dict['Pyexiv2Orientation'] == 6:
                self.queue_operators(['-rotate', '90'])
            elif self.exif_dict['Pyexiv2Orientation'] == 8:
                self.queue_operators(['-rotate', '270'])
            elif self.exif_dict['Pyexiv2Orientation'] == 3:
                self.queue_operators(['-rotate', '180'])

    @property
    def size(self):
        return self.internal_size

    def queue_operators(self, operators):
        self.operators += operators

        self.debug('[IM] Queued operators: %r' % self.operators)

    def run_operators(self, extra_operators):
        command = [
            self.context.config.CONVERT_PATH,
            '-define',
            'tiff:exif-properties=no'  # Otherwise IM treats a bunch of warnings as errors
        ]

        command += self.operators

        command += extra_operators

        returncode, stderr, result = ShellRunner.command(
            command,
            self.context
        )

        return returncode, stderr, result

    def maybe_convert_to_webp(self, jpg_result):
        temp_file = NamedTemporaryFile(delete=False)

        with open(temp_file.name, 'wb') as tmp:
            tmp.write(jpg_result)

        command = [
            self.context.config.CWEBP_PATH,
            temp_file.name,
            '-metadata',
            'all'
        ]

        if self.webp['lossless']:
            command += ['-lossless', '-exact']
        else:
            command += ['-q', '%s' % self.webp['quality']]

        self.webp = False

        command += [
            '-quiet',
            '-o',
            '-'
        ]

        returncode, stderr, webp_result = ShellRunner.command(command,  self.context)

        ShellRunner.rm_f(temp_file.name)

        # If we fail to convert the JPG thumbnail to a WEBP, serve the JPG
        if returncode != 0:
            return jpg_result

        return webp_result

    def debug(self, message):
        logger.debug(message, extra=log_extra(self.context))


Engine.add_format(
    'image/webp',
    '.webp',
    lambda buffer: buffer[:4] == b'RIFF' and buffer[8:12] == b'WEBP'
)
Engine.add_format(
    'image/xcf',
    '.xcf',
    lambda buffer: buffer[:8] == b'gimp xcf'
)
