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
import subprocess
from tempfile import NamedTemporaryFile
from wikimedia_thumbor.shell_runner import ShellRunner

from thumbor.utils import logger


class ExiftoolRunner:
    process = None
    command_file = None

    @classmethod
    def start_process(cls, context):
        if cls.process is not None:
            return

        logger.debug(
            '[ExiftoolRunner] start process with -stay_open'
        )

        start = datetime.datetime.now()

        cls.command_file = NamedTemporaryFile(delete=False)

        command = [
            context.config.EXIFTOOL_PATH,
            '-stay_open',
            'True',
            '-@',
            cls.command_file.name,
        ]

        cls.process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
        )

        duration = datetime.datetime.now() - start

        cls.add_duration_header(context, duration)

    @classmethod
    def stay_open_command(cls, command, context):
        cls.start_process(context)

        logger.debug('[ExiftoolRunner] stay_open_command: %r' % command)
        start = datetime.datetime.now()

        for line in command:
            cls.command_file.write('%s\n' % line)

        cls.command_file.write('-execute\n')
        cls.command_file.flush()

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
