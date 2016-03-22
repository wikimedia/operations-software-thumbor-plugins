#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Stores results in Swift via HTTP

from swiftclient import client
from tornado.concurrent import return_future

from thumbor.result_storages import BaseStorage


class Storage(BaseStorage):
    def __init__(self, context):
        super(Storage, self).__init__(context)

        authurl = (
            'http://' +
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_AUTH_PATH
        )

        self.swift = client.Connection(
            user=self.context.config.SWIFT_USER,
            key=self.context.config.SWIFT_KEY,
            authurl=authurl
        )

    def uri(self):
        return (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_THUMBNAIL_CONTAINER +
            '/' +
            self.context.wikimedia_path
        )

    def put(self, bytes):
        self.swift.put_object(
            self.context.config.SWIFT_THUMBNAIL_CONTAINER,
            self.context.wikimedia_path,
            bytes
        )

    @return_future
    def get(self, callback):
        try:
            headers, data = self.swift.get_object(
                self.context.config.SWIFT_THUMBNAIL_CONTAINER,
                self.context.wikimedia_path
            )
            callback(data)
        except (client.ClientException, AttributeError):
            callback(None)
