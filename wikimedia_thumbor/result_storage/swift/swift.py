#!/usr/bin/python

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2015 Wikimedia Foundation
#
# Stores results in Swift via HTTP

import datetime
import random
import time
from functools import partial

import tornado.ioloop
from swiftclient import client
from swiftclient.exceptions import ClientException
from thumbor.result_storages import BaseStorage, ResultStorageResult
from thumbor.utils import logger

from wikimedia_thumbor.logging import log_extra, record_timing


def thumbnail_expiry(context):
    """How long the thumbnail we're about to store should live, in seconds."""
    config = context.config

    expiry = config.get("SWIFT_THUMBNAIL_EXPIRY_SECONDS", 0)

    if expiry <= 0:
        return None

    if _original_is_new(context):
        # add some jitter
        return int(expiry + random.uniform(0, max(3600, 0)))

    return None


def _original_is_new(context):
    """Was the original this thumbnail comes from uploaded very recently?"""
    age_threshold = context.config.get("SWIFT_THUMBNAIL_RECENCY_AGE_SECONDS", 0)

    if age_threshold <= 0:
        return False

    original_timestamp = getattr(context, "wikimedia_original_timestamp", None)

    if original_timestamp is None:
        return False

    containers = context.config.get("SWIFT_THUMBNAIL_EXPIRY_CONTAINERS", []) or []
    container = getattr(context, "wikimedia_thumbnail_container", None)

    if not container or container not in containers:
        return False

    return time.time() - original_timestamp < age_threshold


class Storage(BaseStorage):
    @property
    def swift(self):
        authurl = self.context.config.SWIFT_HOST + self.context.config.SWIFT_AUTH_PATH

        # This allows us to set the value via config, instead of depending on the
        # x-storage-url header returned by Swift during auth. This is a requirement
        # for communicating with Swift via HTTPS.
        os_options = {"object_storage_url": self.context.config.SWIFT_HOST + self.context.config.SWIFT_API_PATH}

        conn = client.Connection(
            user=self.context.config.SWIFT_PRIVATE_USER if self.context.private else self.context.config.SWIFT_USER,
            key=self.context.config.SWIFT_PRIVATE_KEY if self.context.private else self.context.config.SWIFT_KEY,
            authurl=authurl,
            timeout=self.context.config.SWIFT_CONNECTION_TIMEOUT,
            retries=self.context.config.SWIFT_RETRIES,
            cacert=self.context.config.HTTP_LOADER_CA_CERTS,
            os_options=os_options,
        )

        if self.context.private:
            logger.debug("Setting private connection for result storage", extra=log_extra(self.context))

        return conn

    def uri(self):  # pragma: no cover
        return self.context.config.SWIFT_HOST + self.context.wikimedia_thumbnail_container + "/" + self.context.wikimedia_thumbnail_save_path

    # Coverage strangely reports lines lacking coverage in that function that
    # don't make sense
    async def put(self, bytes):  # pragma: no cover
        self.debug("[SWIFT_STORAGE] put")

        if not hasattr(self.context, "wikimedia_thumbnail_container"):
            return

        try:
            # We store the xkey alongside the object if it's set.
            # This way when an thumbnail falls our of Varnish and is picked
            # up from Swift again, it will have an xkey. Which lets us avoid
            # computing the xkey in Varnish. It always comes from Thumbor.
            xkey = self.context.request_handler._headers.get_list("xkey")
            content_type = self.context.request_handler._headers.get_list("content-type")
            content_disposition = self.context.request_handler._headers.get_list("content-disposition")

            headers = {}

            if len(content_disposition):
                headers["Content-Disposition"] = content_disposition[0]

            if len(xkey):
                headers["Xkey"] = xkey[0]

            expiry = thumbnail_expiry(self.context)

            if expiry is not None:
                headers["X-Delete-After"] = str(expiry)

            content_type = content_type[0] if len(content_type) else None

            start = datetime.datetime.now()

            await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                partial(
                    self.swift.put_object,
                    self.context.wikimedia_thumbnail_container,
                    self.context.wikimedia_thumbnail_save_path,
                    bytes,
                    headers=headers,
                    content_type=content_type,
                ),
            )
            record_timing(self.context, datetime.datetime.now() - start, "swift.thumbnail.write.success")

            # We cannot set the time spent in putting to swift in the response
            # headers, because the response has already been sent when saving
            # to Swift happens (which is the right thing to do).
        except AssertionError as e:
            # Let assertion errors go through for tests
            raise e
        except Exception as e:
            record_timing(self.context, datetime.datetime.now() - start, "swift.thumbnail.write.exception")
            self.error(f"[SWIFT_STORAGE] put exception: {e!r}")
            # We cannnot let exceptions bubble up, because they would leave
            # the client's connection hanging

    async def get(self):
        self.debug(f"[SWIFT_STORAGE] get: {self.context.wikimedia_thumbnail_container!r} {self.context.wikimedia_thumbnail_save_path!r}")

        try:
            # swiftclient has this annoying habit of writing an ERROR log
            # entry for the ClientException, regardless of it being caught

            start = datetime.datetime.now()

            conn = self.swift
            headers, data = await tornado.ioloop.IOLoop.current().run_in_executor(
                None,
                partial(
                    conn.get_object,
                    self.context.wikimedia_thumbnail_container,
                    self.context.wikimedia_thumbnail_save_path,
                ),
            )

            record_timing(self.context, datetime.datetime.now() - start, "swift.thumbnail.read.success", "Thumbor-Swift-Thumbnail-Success-Time")

            self.debug("[SWIFT_STORAGE] found")
            return ResultStorageResult(buffer=data, metadata=headers)
        # We want this to be exhaustive because not catching an exception here
        # would result in the request hanging indefinitely
        except ClientException:
            # logging.disable(logging.NOTSET)
            record_timing(self.context, datetime.datetime.now() - start, "swift.thumbnail.read.miss", "Thumbor-Swift-Thumbnail-Miss-Time")
            # No need to log this one, it's expected behavior when the
            # requested object isn't there
            self.debug("[SWIFT_STORAGE] missing")
            return None
        except AssertionError as e:
            # Let assertion errors go through for tests
            raise e
        except Exception as e:
            # logging.disable(logging.NOTSET)
            record_timing(self.context, datetime.datetime.now() - start, "swift.thumbnail.read.exception", "Thumbor-Swift-Thumbnail-Exception-Time")
            self.error(f"[SWIFT_STORAGE] get exception: {e!r}")
            return None

    def debug(self, message):
        logger.debug(message, extra=log_extra(self.context))

    def error(self, message):
        logger.error(message, extra=log_extra(self.context))
