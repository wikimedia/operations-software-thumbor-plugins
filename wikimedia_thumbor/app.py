#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2016 Wikimedia Foundation

import manhole

from thumbor.utils import logger

from tc_core.app import App as CommunityCoreApp


class App(CommunityCoreApp):
    def __init__(self, context):
        if context.config.get('MANHOLE_DEBUGGING', None):
            logger.debug("Installing manhole")
            manhole.install()

        super(App, self).__init__(context)
