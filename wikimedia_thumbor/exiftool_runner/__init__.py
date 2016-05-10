#!/usr/bin/python
# -*- coding: utf-8 -*-

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


import datetime
import errno
import os
import subprocess
from tempfile import NamedTemporaryFile

from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner


class ExiftoolRunner:
    process = None
    fifo = None
    fifo_name = None

    @classmethod
    def start_process(cls, context):
        if cls.process is not None:
            return

        logger.debug(
            '[ExiftoolRunner] start process with -stay_open'
        )

        start = datetime.datetime.now()

        # Create a temp file just to get a proper temp file name
        temp_file = NamedTemporaryFile()
        cls.fifo_name = temp_file.name
        # Close the temp file, which deletes it
        temp_file.close()
        # Create a named pipe in place of the old temp file
        os.mkfifo(cls.fifo_name)

        command = [
            context.config.EXIFTOOL_PATH,
            '-stay_open',
            'True',
            '-@',
            cls.fifo_name,
        ]

        cls.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        # We need to wait until exiftool is reading before we
        # open the fifo as write-only. Otherwise open() hangs, waiting
        # for a reader to show up.
        cls.fifo = open(cls.fifo_name, 'w', 0)

        logger.debug('[ExiftoolRunner] process started in %r' % duration)

    @classmethod
    def stay_open_command(cls, command, context):
        cls.start_process(context)

        logger.debug('[ExiftoolRunner] stay_open_command: %r' % command)
        start = datetime.datetime.now()

        for line in command:
            cls.fifo.write('%s\n' % line)

        cls.fifo.write('-execute\n')

        stdout = ''
        line = ''
        marker = '{ready}\n'

        while not line.endswith(marker):
            line = cls.process.stdout.readline()
            if line.endswith(marker):
                stdout += line[:-len(marker)]
            else:
                stdout += line

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        return stdout

    @classmethod
    def classic_command(cls, command, context):
        command.insert(0, context.config.EXIFTOOL_PATH)

        logger.debug('[ExiftoolRunner] classic_command: %r' % command)
        start = datetime.datetime.now()

        code, stderr, stdout = ShellRunner.command(command, context)

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

        return stdout

    @classmethod
    def add_duration_header(cls, context, duration):
        duration = int(round(duration.total_seconds() * 1000, 0))

        context.request_handler.add_header(
            'Exiftool-Time',
            duration
        )

    @classmethod
    def command(cls, command, context):
        try:
            if context.config.EXIFTOOL_STAY_OPEN:
                return cls.stay_open_command(command, context)
        except AttributeError:
            pass

        return cls.classic_command(command, context)

    @classmethod
    def cleanup(cls):
        if cls.process:
            logger.debug('[ExiftoolRunner] killing process')
            cls.process.kill()
            cls.process = None

        if cls.fifo:
            logger.debug('[ExiftoolRunner] closing named pipe')
            cls.fifo.close()
            cls.fifo = None

        if cls.fifo_name:
            if os.path.exists(cls.fifo_name):
                try:
                    os.unlink(cls.fifo_name)
                    logger.debug('[ExiftoolRunner] unlinking named pipe')
                except OSError as e:
                    if e.errno != errno.ENOENT:
                        raise

            cls.fifo_name = None
