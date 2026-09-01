#!/usr/bin/python

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Utility class to run exiftool commands
#
#
# They can either run as one-off commands or using a long-running
# exiftool process started with the -stay_open option.
#
# Since Thumbor is single-threaded, there is no need for locking
# nor having multiple exiftool processes.


from tempfile import NamedTemporaryFile

from thumbor.utils import logger

from wikimedia_thumbor.logging import log_extra
from wikimedia_thumbor.shell_runner import ShellRunner


class ExiftoolRunner:
    @classmethod
    def command(
        cls,
        context,
        pre=None,
        post=None,
        buffer='',
        input_temp_file=None
    ):
        pre = pre or []
        post = post or []

        if not input_temp_file:
            input_temp_file = NamedTemporaryFile()
            input_temp_file.write(buffer)
            input_temp_file.flush()

        command = [context.config.EXIFTOOL_PATH]
        command += pre
        # Avoids warnings going to stdout or stderr
        command += ['-m', '-q', '-q']
        command.append(input_temp_file.name)
        command += post

        logger.debug(f'[ExiftoolRunner] command: {command!r}', extra=log_extra(context))

        code, stderr, stdout = ShellRunner.command(command, context)

        input_temp_file.close()

        if stderr:
            logger.error(f'[ExiftoolRunner] error: {stderr!r}', extra=log_extra(context))

        return stdout
