#!/usr/bin/python

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Simply stores originals in a local dictionary
# In practice this deliberately shouldn't work
# across requests, unless the same instance of this class
# is passed between requests (which is the case for /multi)

from thumbor.storages import BaseStorage
from thumbor.utils import logger


class Storage(BaseStorage):
    def __init__(self, context):
        BaseStorage.__init__(self, context)
        self.dict = {}

    def put(self, path, contents):
        logger.debug(f"[REQUEST_STORAGE] put: {path}")
        self.dict[path] = contents
        return path

    def put_crypto(self, path):
        return path

    async def exists(self, path):
        return path in self.dict

    async def get(self, path):
        logger.debug(f"[REQUEST_STORAGE] get: {path}")
        try:
            value = self.dict[path]
            logger.debug("[REQUEST_STORAGE] found")
            return value
        except KeyError:
            logger.debug("[REQUEST_STORAGE] missing")
            return None
