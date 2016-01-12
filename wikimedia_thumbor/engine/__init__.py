#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Base engine, not to be used directly, has to be extended

import errno
import os
import subprocess
from tempfile import NamedTemporaryFile

from thumbor.engines.pil import Engine as PilEngine
from thumbor.utils import logger


def rm_f(path):
    """Remove a file if it exists."""
    try:
        os.unlink(path)
    except OSError as e:
        if e.errno != errno.ENOENT:
            raise


class BaseWikimediaEngine(PilEngine):
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
        rm_f(self.source.name)
        rm_f(self.destination.name)

    def exec_command(self, command):
        self.command(command)

        with open(self.destination.name, 'rb') as f:
            result = f.read()

        self.cleanup_temp_files()

        return result

    def command(self, command):
        wrapped_command = command

        try:
            cgroup = self.context.config.SUBPROCESS_CGROUP
            cgexec_path = self.context.config.SUBPROCESS_CGEXEC_PATH
            wrapped_command = [
                cgexec_path,
                '-g',
                cgroup
            ] + wrapped_command
        except AttributeError:
            pass

        try:
            timeout = self.context.config.SUBPROCESS_TIMEOUT
            timeout_path = self.context.config.SUBPROCESS_TIMEOUT_PATH
            wrapped_command = [
                timeout_path,
                '%s' % timeout
            ] + wrapped_command
        except AttributeError:
            pass

        logger.debug('Command: %r' % wrapped_command)

        p = subprocess.Popen(
            wrapped_command,
            stdout=subprocess.PIPE
        )
        stdout, stderr = p.communicate()

        logger.debug('Stdout: %s' % stdout)
        logger.debug('Stderr: %s' % stderr)
        logger.debug('Return code: %d' % p.returncode)

        if p.returncode != 0:
            self.cleanup_temp_files()
            raise Exception(
                'CommandError',
                wrapped_command,
                stdout,
                stderr,
                p.returncode
            )

        return stdout
