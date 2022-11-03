#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2017 Wikimedia Foundation

# PoolCounter client

import socket

import tornado.iostream

from thumbor.utils import logger
from wikimedia_thumbor.logging import log_extra


class PoolCounter:
    def __init__(self, context):
        self.server = context.config.POOLCOUNTER_SERVER
        self.port = context.config.get('POOLCOUNTER_PORT', 7531)
        self.context = context
        self.stream = None

    async def connect(self):
        self.debug('[PoolCounter] Connecting to: %s %d' % (self.server, self.port))
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
        self.stream = tornado.iostream.IOStream(s)
        await self.stream.connect((self.server, self.port))

    async def acq4me(self, key, workers, maxqueue, timeout):
        if not self.stream:
            await self.connect()

        try:
            self.debug('[PoolCounter] ACQ4ME %s %d %d %d' % (key, workers, maxqueue, timeout))
            await self.stream.write('ACQ4ME %s %d %d %d\n' % (key, workers, maxqueue, timeout))
            data = await self.stream.read_until('\n')
        except socket.error as e:
            self.stream = None
            raise e

        return data == 'LOCKED\n'

    async def release(self):
        if not self.stream:
            await self.connect()

        try:
            self.debug('[PoolCounter] RELEASE')
            await self.stream.write('RELEASE\n')
            data = await self.stream.read_until('\n')
        except socket.error as e:
            self.stream = None
            raise e

        return data == 'RELEASED\n'

    def close(self):
        if self.stream:
            self.debug('[PoolCounter] Disconnecting')
            self.stream.close()
            self.stream = None
            return True
        else:
            self.debug('[PoolCounter] Already disconnected')
            return False

    def debug(self, message):
        logger.debug(message, extra=log_extra(self.context))
