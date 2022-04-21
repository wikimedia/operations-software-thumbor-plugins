#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2022 Wikimedia Foundation

from thumbor.app import ThumborServiceApp
from thumbor.handlers import ContextHandler
from thumbor.utils import logger
from wikimedia_thumbor.core import Extensions
from wikimedia_thumbor.core.context import Context
from wikimedia_thumbor.core.importer import Importer


class App(ThumborServiceApp):

    def __init__(self, context):
        '''
        :param context: `Context` instance
        '''

        if context.config.get('COMMUNITY_EXTENSIONS', None):
            for extension in context.config.get('COMMUNITY_EXTENSIONS'):
                Extensions.load(extension)

        Importer.import_community_modules(context.modules.importer)

        self.context = Context.from_context(context)

        if self.context.config.get('COMMUNITY_MONKEYPATCH', True):
            logger.debug("Monkey patching ContextHandler.initialize")
            # Monkey patch the ContextHandler.initialize method to generate a
            # community context instead of the one from vanilla thumbor.

            def initialize(self, context):
                '''Initialize a new Context object
                :param context: thumbor.context.Context
                '''
                self.context = Context.from_context(
                    context,
                    request_handler=self
                )

            ContextHandler.initialize = initialize

        super(App, self).__init__(context)

    def get_handlers(self):
        '''Return a list of tornado web handlers.
        '''

        handlers = []

        for extensions in Extensions.extensions:
            for handler in extensions.handlers:

                # Inject the context if the handler expects it.
                if issubclass(handler[1], ContextHandler):
                    if len(handler) < 3:
                        handler = list(handler)
                        handler.append(dict(context=self.context))
                    else:
                        handler[2]['context'] = self.context

                handlers.append(handler)

        handlers.extend(super(App, self).get_handlers())

        return handlers
