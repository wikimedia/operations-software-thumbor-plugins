# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler translates mediawiki thumbnail urls into thumbor urls
# And sets the xkey for Varnish purging purposes

from urllib import quote
import json
import tornado.gen as gen

from thumbor.context import RequestParameters
from thumbor.handlers import BaseHandler
from thumbor.handlers.imaging import ImagingHandler
from thumbor.utils import logger


old_error = BaseHandler._error


# We need to monkey-patch BaseHandler because otherwise we
# wouldn't apply the Cache-Control headers to 400 errors that
# don't make it to ImagesHandler since they don't match the
# handlers' regexp.
def _error(self, status, msg=None):
    # Errors should explicitely not be cached
    self.set_header(
        'Cache-Control',
        'no-cache'
    )
    self.clear_header('xkey')
    self.clear_header('Content-Disposition')
    self.clear_header('Wikimedia-Original-Container')
    self.clear_header('Wikimedia-Thumbnail-Container')
    self.clear_header('Wikimedia-Original-Path')
    self.clear_header('Wikimedia-Thumbnail-Path')
    self.clear_header('Thumbor-Parameters')
    old_error(self, status, msg)


BaseHandler._error = _error


class TranslateError(Exception):
    pass


class ImagesHandler(ImagingHandler):
    @classmethod
    def regex(cls):
        return (
            r'/'
            r'(?P<project>[^-/]+)/'
            r'(?P<language>[^/]+)/'
            r'thumb/'
            r'(?:(?P<specialpath>temp|archive)/)?'
            r'(?P<shard1>[0-9a-zA-Z]+)/'
            r'(?P<shard2>[0-9a-zA-Z]+)/'
            r'(?P<filename>[^/]+)\.'
            r'(?P<extension>[^/]+)/'
            r'(?:(?P<qlow>qlow-))?'
            r'(?:(?P<lossy>lossy-))?'
            r'(?:(?P<lossless>lossless-))?'
            r'(?:page(?P<page>\d+)-)?'
            r'(?:lang(?P<lang>[a-zA-Z]+)-)?'
            r'(?P<width>\d+)px-'
            r'(?:seek=(?P<seek>\d+)-)?'
            r'(?P<end>[^/]+)'
            r'\.(?P<format>[a-zA-Z]+)'
        )

    def generate_save_swift_path(self, kw):
        path = '/'.join(
            (
                kw['shard1'],
                kw['shard2'],
                kw['filename'] + '.' + kw['extension'],
                ''
            )
        )

        if kw['specialpath']:
            path = '/'.join((kw['specialpath'], path))

        if kw['qlow'] == 'qlow-':
            path += kw['qlow']

        if kw['lossy'] == 'lossy-':  # pragma: no cover
            path += kw['lossy']

        if kw['lossless'] == 'lossless-':
            path += kw['lossless']

        if kw['page']:
            path += 'page' + kw['page'] + '-'

        if kw['lang']:
            path += 'lang' + kw['lang'] + '-'

        path += kw['width'] + 'px-'

        if kw['seek']:
            path += 'seek=' + kw['seek'] + '-'

        path += kw['end']

        path += '.' + kw['format']

        return path

    def translate(self, kw):
        logger.debug('[ImagesHandler] translate: %r' % kw)

        filepath = '/'.join(
            (
                kw['shard1'],
                kw['shard2'],
                kw['filename'] + '.' + kw['extension']
            )
        )

        if kw['specialpath']:
            filepath = '/'.join((kw['specialpath'], filepath))

        translated = {'width': kw['width']}

        if int(kw['width']) < 1:
            raise TranslateError('Width requested must be at least 1')

        sharded_containers = []

        if hasattr(self.context.config, 'SWIFT_SHARDED_CONTAINERS'):
            sharded_containers = self.context.config.SWIFT_SHARDED_CONTAINERS

        project = kw['project']
        language = kw['language']

        # Handle sharding check before legacy projlang override
        projlang = '-'.join((project, language))
        original_container = projlang + '-local-public'
        thumbnail_container = projlang + '-local-thumb'
        shard = '.' + kw['shard2']

        if original_container in sharded_containers:
            original_container += shard

        if thumbnail_container in sharded_containers:
            thumbnail_container += shard

        swift_uri = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_API_PATH +
            original_container
        )

        swift_uri += '/'

        translated['image'] = swift_uri + filepath

        filters = []

        if kw['format'].lower() in ('jpe', 'jpeg'):
            kw['format'] = 'jpg'

        if kw['extension'].lower() in ('jpg', 'jpe', 'jpeg'):
            if (
                kw['qlow'] == 'qlow-' and
                hasattr(self.context.config, 'QUALITY_LOW')
            ):
                logger.debug('[ImagesHandler] apply JPG low quality')
                filters.append('quality(%d)' % self.context.config.QUALITY_LOW)

            if hasattr(self.context.config, 'DEFAULT_FILTERS_JPEG'):
                logger.debug('[ImagesHandler] apply JPG default filters')
                filters.append(self.context.config.DEFAULT_FILTERS_JPEG)

        filters.append('format(%s)' % kw['format'])

        page = kw.get('page')

        if not page:
            page = kw.get('seek')

        if page:
            filters.append('page(%s)' % page)

        lang = kw.get('lang')

        if lang:
            filters.append('lang(%s)' % lang)

        if filters:
            translated['filters'] = ':'.join(filters)

        try:
            self.context.request_handler.set_header(
                'xkey',
                u'File:' + kw['filename'] + u'.' + kw['extension']
            )

            self.context.request_handler.set_header(
                'Content-Disposition',
                u'inline;filename*=UTF-8\'\'%s.%s' % (
                    kw['filename'],
                    kw['extension']
                )
            )
        except ValueError as e:
            logger.debug('[ImagesHandler] Skip setting invalid header: %r', e)

        # Save wikimedia-specific save path information
        # Which will later be used by result storage
        self.context.wikimedia_thumbnail_container = thumbnail_container
        self.context.wikimedia_thumbnail_save_path = \
            self.generate_save_swift_path(kw)

        if hasattr(self.context.config, 'SWIFT_PATH_PREFIX'):
            self.context.wikimedia_thumbnail_save_path = (
                self.context.config.SWIFT_PATH_PREFIX +
                self.context.wikimedia_thumbnail_save_path
            )

        try:
            self.context.request_handler.set_header(
                'Wikimedia-Thumbnail-Container',
                self.context.wikimedia_thumbnail_container
            )

            self.context.request_handler.set_header(
                'Wikimedia-Path',
                self.context.wikimedia_thumbnail_save_path
            )

            self.context.request_handler.set_header(
                'Thumbor-Parameters',
                json.dumps(translated)
            )
        except ValueError as e:
            logger.debug('[ImagesHandler] Skip setting invalid header: %r', e)

        return translated

    @gen.coroutine
    def check_image(self, kw):
        try:
            translated_kw = self.translate(kw)
        except TranslateError as e:
            self._error(
                400,
                str(e)
            )
            return

        if self.context.config.MAX_ID_LENGTH > 0:
            # Check if an image with an uuid exists in storage
            image = translated_kw['image']
            truncated_image = image[:self.context.config.MAX_ID_LENGTH]
            maybe_future = self.context.modules.storage.exists(truncated_image)
            exists = yield gen.maybe_future(maybe_future)
            if exists:  # pragma: no cover
                translated_kw['image'] = truncated_image

        translated_kw['image'] = quote(translated_kw['image'].encode('utf-8'))
        if not self.validate(translated_kw['image']):  # pragma: no cover
            self._error(
                400,
                'No original image was specified in the given URL'
            )
            return

        translated_kw['request'] = self.request
        self.context.request = RequestParameters(**translated_kw)

        self.execute_image_operations()
