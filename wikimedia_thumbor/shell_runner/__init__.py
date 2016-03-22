#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# Utility class to run shell commands safely

import datetime
import errno
import os
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
    def command(cls, command, context, stdin=None, env=None):
        start = datetime.datetime.now()

        wrapped_command = ShellRunner.wrap_command(
            command,
            context
        )

        logger.debug('Command: %r' % wrapped_command)

        combined_env = os.environ.copy()

        if env is not None:
            combined_env.update(env)

        if stdin is None:
            p = subprocess.Popen(
                wrapped_command,
                stdout=subprocess.PIPE,
                env=combined_env
            )
        else:
            p = subprocess.Popen(
                wrapped_command,
                stdout=subprocess.PIPE,
                stdin=subprocess.PIPE,
                env=combined_env
            )
            p.stdin.write(stdin)

        stdout, stderr = p.communicate()

        duration = datetime.datetime.now() - start
        duration = duration.total_seconds() * 1000

        length = len(stdout)

        if length > 1000:
            logger.debug('Stdout: <too long to display (%d bytes)>' % length)
        else:
            logger.debug('Stdout: %s' % stdout)

        logger.debug('Stderr: %s' % stderr)
        logger.debug('Return code: %d' % p.returncode)
        logger.debug('Duration: %r' % duration)

        return p.returncode, stderr, stdout

    @classmethod
    def rm_f(cls, path):
        """Remove a file if it exists."""
        try:
            os.unlink(path)
        except OSError as e:
            if e.errno != errno.ENOENT:
                raise
