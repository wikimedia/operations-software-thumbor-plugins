#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Base engine, not to be used directly, has to be extended

from tempfile import NamedTemporaryFile
from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner
from wikimedia_thumbor.engine.imagemagick import Engine as IMEngine


class BaseWikimediaEngine(IMEngine):
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

    def prepare_temp_files(self, buffer):
        self.destination = NamedTemporaryFile(delete=False)
        self.source = NamedTemporaryFile(delete=False)
        self.source.write(buffer)
        self.source.close()

    def cleanup_temp_files(self):
        ShellRunner.rm_f(self.source.name)
        ShellRunner.rm_f(self.destination.name)

    def command(self, command, env=None):
        returncode, stderr, stdout = ShellRunner.command(
            command,
            self.context,
            env=env
        )

        if returncode != 0:
            self.cleanup_temp_files()
            raise Exception(
                'CommandError',
                command,
                stdout,
                stderr,
                returncode
            )

        return stdout

    def exec_command(self, command, env=None):
        self.command(command, env)

        with open(self.destination.name, 'rb') as f:
            result = f.read()

        self.cleanup_temp_files()

        return result

    def read(self, extension=None, quality=None):
        # read() is sometimes used to read back the original.
        # This relies on the convention that any engine extending
        # BaseWikimediaEngine should set original_buffer inside its
        # create_image method
        if (
            hasattr(self, 'original_buffer') and
            quality is None and
            extension == self.extension
        ):
            logger.debug('[BWE] Reading the original')
            return self.original_buffer

        # When requests don't come through the wikimedia url handler
        # and the format isn't specified, we default to JPG output
        if self.context.request.format is None:
            logger.debug('[BWE] Defaulting to .jpg')
            extension = '.jpg'
        else:
            extension = self.context.request.format
            logger.debug('[BWE] Rendering %s' % extension)

        return super(BaseWikimediaEngine, self).read(extension, quality)
