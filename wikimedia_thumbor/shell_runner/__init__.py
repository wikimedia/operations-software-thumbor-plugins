#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Utility class to run shell commands safely

import subprocess

from thumbor.utils import logger


class ShellRunner:
    @classmethod
    def wrap_command(cls, command, context):
        wrapped_command = command

        try:
            cgroup = context.config.SUBPROCESS_CGROUP
            cgexec_path = context.config.SUBPROCESS_CGEXEC_PATH
            wrapped_command = [
                cgexec_path,
                '-g',
                cgroup
            ] + wrapped_command
        except AttributeError:
            pass

        try:
            timeout = context.config.SUBPROCESS_TIMEOUT
            timeout_path = context.config.SUBPROCESS_TIMEOUT_PATH
            wrapped_command = [
                timeout_path,
                '--foreground',
                '%s' % timeout
            ] + wrapped_command
        except AttributeError:
            pass

        return wrapped_command

    @classmethod
    def command(cls, command, context):
        wrapped_command = ShellRunner.wrap_command(
            command,
            context
        )

        logger.debug('Command: %r' % wrapped_command)

        p = subprocess.Popen(
            wrapped_command,
            stdout=subprocess.PIPE
        )
        stdout, stderr = p.communicate()

        logger.debug('Stdout: %s' % stdout)
        logger.debug('Stderr: %s' % stderr)
        logger.debug('Return code: %d' % p.returncode)

        return p.returncode, stderr, stdout
