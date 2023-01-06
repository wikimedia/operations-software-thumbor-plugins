#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Stores results in Swift via HTTP

import datetime
# import logging
import random

from swiftclient import client
from swiftclient.exceptions import ClientException

from thumbor.result_storages import BaseStorage, ResultStorageResult
from thumbor.utils import logger

from wikimedia_thumbor.logging import record_timing, log_extra


class Storage(BaseStorage):
    swiftconn = None
    swiftconn_private = None

    @property
    def swift(self):
        if self.context.private:
            if Storage.swiftconn_private:
                return Storage.swiftconn_private
        else:
            if Storage.swiftconn:
                return Storage.swiftconn

        authurl = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_AUTH_PATH
        )

        # This allows us to set the value via config, instead of depending on the
        # x-storage-url header returned by Swift during auth. This is a requirement
        # for communicating with Swift via HTTPS.
        os_options = {
            'object_storage_url': self.context.config.SWIFT_HOST + self.context.config.SWIFT_API_PATH
        }

        conn = client.Connection(
            user=self.context.config.SWIFT_PRIVATE_USER if self.context.private else self.context.config.SWIFT_USER,
            key=self.context.config.SWIFT_PRIVATE_KEY if self.context.private else self.context.config.SWIFT_KEY,
            authurl=authurl,
            timeout=self.context.config.SWIFT_CONNECTION_TIMEOUT,
            retries=self.context.config.SWIFT_RETRIES,
            cacert=self.context.config.HTTP_LOADER_CA_CERTS,
            os_options=os_options
        )

        if self.context.private:
            Storage.swiftconn_private = conn
        else:
            Storage.swiftconn = conn

        return conn

    def uri(self):  # pragma: no cover
        return (
            self.context.config.SWIFT_HOST +
            self.context.wikimedia_thumbnail_container +
            '/' +
            self.context.wikimedia_thumbnail_save_path
        )

    # Coverage strangely reports lines lacking coverage in that function that
    # don't make sense
    async def put(self, bytes):  # pragma: no cover
        self.debug('[SWIFT_STORAGE] put')

        if not hasattr(self.context, 'wikimedia_thumbnail_container'):
            return

        try:
            # We store the xkey alongside the object if it's set.
            # This way when an thumbnail falls our of Varnish and is picked
            # up from Swift again, it will have an xkey. Which lets us avoid
            # computing the xkey in Varnish. It always comes from Thumbor.
            xkey = self.context.request_handler._headers.get_list('xkey')
            content_type = self.context.request_handler._headers.get_list('content-type')
            content_disposition = self.context.request_handler._headers.get_list('content-disposition')

            headers = {}

            if len(content_disposition):
                headers['Content-Disposition'] = content_disposition[0]

            if len(xkey):
                headers['Xkey'] = xkey[0]

            expiry = self.context.config.get('SWIFT_THUMBNAIL_EXPIRY_SECONDS', 0)
            sampling_factor = self.context.config.get('SWIFT_THUMBNAIL_EXPIRY_SAMPLING_FACTOR', 0)

            if expiry > 0 and sampling_factor > 0 and random.randint(1, sampling_factor) == 1:
                headers['X-Delete-After'] = expiry

            content_type = content_type[0] if len(content_type) else None

            start = datetime.datetime.now()
            self.swift.put_object(
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_thumbnail_save_path,
                bytes,
                headers=headers,
                content_type=content_type
            )
            record_timing(self.context, datetime.datetime.now() - start, 'swift.thumbnail.write.success')

            # We cannot set the time spent in putting to swift in the response
            # headers, because the response has already been sent when saving
            # to Swift happens (which is the right thing to do).
        except AssertionError as e:
            # Let assertion errors go through for tests
            raise e
        except Exception as e:
            record_timing(self.context, datetime.datetime.now() - start, 'swift.thumbnail.write.exception')
            self.error('[SWIFT_STORAGE] put exception: %r' % e)
            # We cannnot let exceptions bubble up, because they would leave
            # the client's connection hanging

    async def get(self):
        self.debug('[SWIFT_STORAGE] get: %r %r' % (
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_thumbnail_save_path
            )
        )

        try:
            # swiftclient has this annoying habit of writing an ERROR log
            # entry for the ClientException, regardless of it being caught

            start = datetime.datetime.now()

            # hnowlan: Temporarily disable log disabling here in case we're missing a valid exception
            # logging.disable(logging.ERROR)
            headers, data = self.swift.get_object(
                self.context.wikimedia_thumbnail_container,
                self.context.wikimedia_thumbnail_save_path
            )
            # hnowlan: Temporarily disable log disabling here in case we're missing a valid exception
            # logging.disable(logging.NOTSET)

            record_timing(self.context, datetime.datetime.now() - start, 'swift.thumbnail.read.success', 'Thumbor-Swift-Thumbnail-Success-Time')

            self.debug('[SWIFT_STORAGE] found')
            return ResultStorageResult(buffer=data, metadata=headers)
        # We want this to be exhaustive because not catching an exception here
        # would result in the request hanging indefinitely
        except ClientException:
            # logging.disable(logging.NOTSET)
            record_timing(self.context, datetime.datetime.now() - start, 'swift.thumbnail.read.miss', 'Thumbor-Swift-Thumbnail-Miss-Time')
            # No need to log this one, it's expected behavior when the
            # requested object isn't there
            self.debug('[SWIFT_STORAGE] missing')
            return None
        except AssertionError as e:
            # Let assertion errors go through for tests
            raise e
        except Exception as e:
            # logging.disable(logging.NOTSET)
            record_timing(self.context, datetime.datetime.now() - start, 'swift.thumbnail.read.exception', 'Thumbor-Swift-Thumbnail-Exception-Time')
            self.error('[SWIFT_STORAGE] get exception: %r' % e)
            return None

    def debug(self, message):
        logger.debug(message, extra=log_extra(self.context))

    def error(self, message):
        logger.error(message, extra=log_extra(self.context))
