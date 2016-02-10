# -*- coding: utf-8 -*-

# Copyright (c) 2016, thumbor-community, Wikimedia Foundation
# Use of this source code is governed by the MIT license that can be
# found in the LICENSE file.
#
# This handler translates mediawiki thumbnail urls into thumbor urls
# And sets the xkey for Varnish purging purposes

import tornado.web

from thumbor.handlers.imaging import ImagingHandler


class ImagesHandler(ImagingHandler):
    @classmethod
    def regex(cls):
        return (
            r'/images/thumb/'
            r'(?P<filepath>[0-9a-z]+/[0-9a-z]+/)'
            r'(?P<filename>.*)\.(?P<extension>.*)/'
            r'(?:(?P<qlow>qlow-))?'
            r'(?:(?P<lossy>lossy-))?'
            r'(?:page(?P<page>\d+)-)?'
            r'(?P<width>\d+)px-'
            r'(?:(?P<seek>\d+)-)?'
            r'.*'
        )

    @tornado.web.asynchronous
    def get(self, **kw):
        translated_kw = self.translate(kw)
        return super(ImagesHandler, self).get(**translated_kw)

    @tornado.web.asynchronous
    def head(self, **kw):
        translated_kw = self.translate(kw)
        return super(ImagesHandler, self).head(**translated_kw)

    def translate(self, kw):
        filename = '%(filename)s.%(extension)s' % kw
        filepath = kw['filepath'] + filename

        translated = {'unsafe': 'unsafe'}
        translated['width'] = kw['width']

        swift_uri = (
            self.context.config.SWIFT_HOST +
            self.context.config.SWIFT_API_PATH +
            self.context.config.SWIFT_ORIGINAL_CONTAINER +
            '/'
        )

        translated['image'] = swift_uri + filepath

        filters = []

        if kw['extension'] in ('jpg', 'jpe', 'jpeg'):
            if (
                kw['qlow'] == 'qlow-' and
                hasattr(self.context.config, 'QUALITY_LOW')
            ):
                filters.append('quality(%d)' % self.context.config.QUALITY_LOW)

            if hasattr(self.context.config, 'DEFAULT_FILTERS_JPEG'):
                filters.append(self.context.config.DEFAULT_FILTERS_JPEG)

        page = kw.get('page', kw['seek'])

        if page:
            filters.append('page(%s)' % page)

        if filters:
            translated['filters'] = ':'.join(filters)

        self.context.request_handler.set_header(
            'xkey',
            u'File:' + filename
        )

        return translated
