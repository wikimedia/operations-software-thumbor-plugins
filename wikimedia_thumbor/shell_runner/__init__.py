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
from functools import partial
import os
import re
import subprocess
import math

from thumbor.utils import logger
from wikimedia_thumbor.logging import log_extra


class ShellRunner:
    @classmethod
    def wrap_command(cls, command, context):
        if not getattr(context.config, "SUBPROCESS_USE_TIMEOUT", False):
            return command

        timeout = context.config.SUBPROCESS_TIMEOUT
        timeout_path = context.config.SUBPROCESS_TIMEOUT_PATH

        timeout_command = [
                timeout_path,
                "--foreground"
        ]
        # The timeout command sends a SIGTERM signal by default.
        # --kill-after tells timeout to send a SIGKILL signal if the
        # command is still running after the initial SIGTERM was sent.
        # A value of 0 disables this.
        kill_after = getattr(context.config, "SUBPROCESS_TIMEOUT_KILL_AFTER", 0)
        if kill_after > 0:
            timeout_command.extend(["--kill-after", f"{kill_after}s"])

        # Add the timeout, format is timeout $TIMEOUT_ARGS $TIMEOUT_TIME $ACTUAL_COMMAND $ACTUAL_ARGS
        timeout_command.append(str(timeout))
        command = timeout_command + command

        return command

    @classmethod
    def preexec(cls, context):  # pragma: no cover
        if not getattr(context.config, "SUBPROCESS_CGROUP_TASKS_PATH", False):
            return

        pid = os.getpid()

        cls.debug(context, "[ShellRunner] Adding pid %r to cgroup" % pid)

        with open(context.config.SUBPROCESS_CGROUP_TASKS_PATH, "a+") as tasks:
            tasks.write("%s\n" % pid)

    @classmethod
    def popen(cls, command, context, env=None):
        wrapped_command = ShellRunner.wrap_command(command, context)

        cls.debug(context, "[ShellRunner] Command: %r" % wrapped_command)

        combined_env = os.environ.copy()

        if env is not None:  # pragma: no cover
            combined_env.update(env)

        proc = subprocess.Popen(
            wrapped_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=combined_env,
            preexec_fn=partial(cls.preexec, context),
        )

        return proc

    @classmethod
    def command(cls, command, context, env=None):
        start = datetime.datetime.now()

        proc = cls.popen(command, context, env)

        stdout, stderr = proc.communicate()

        duration = datetime.datetime.now() - start
        duration = duration.total_seconds() * 1000

        length = len(stdout)

        if length > 1000:
            cls.debug(
                context,
                "[ShellRunner] Stdout: <too long to display (%d bytes)>" % length,
            )
        else:
            cls.debug(context, "[ShellRunner] Stdout: %s" % stdout)

        cls.debug(context, "[ShellRunner] Stderr: %s" % stderr)
        cls.debug(context, "[ShellRunner] Return code: %d" % proc.returncode)
        cls.debug(context, "[ShellRunner] Duration: %r" % duration)

        simple_command_name = os.path.basename(command[0])
        simple_command_name = re.sub(r"[^a-zA-Z0-9-]", r"", simple_command_name)

        if context.request_handler is not None:
            context.request_handler.add_header(
                "Thumbor-%s-Time" % simple_command_name,
                # In order to copy Python 2 behaviour of round() method, namely "round
                # half away from zero" rounding, method math.floor() and adding 0.5 to
                # the value which will be rounded are used.
                math.floor(duration + 0.5),
            )

        return proc.returncode, stderr, stdout

    @classmethod
    def rm_f(cls, path):
        """Remove a file if it exists."""
        try:
            os.unlink(path)
        except OSError as e:  # pragma: no cover
            if e.errno != errno.ENOENT:
                raise

    @classmethod
    def debug(cls, context, message):
        logger.debug(message, extra=log_extra(context))
