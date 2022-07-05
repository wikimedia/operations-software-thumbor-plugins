#!/usr/bin/python
# -*- coding: utf-8 -*-

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2017, thumbor-community

import importlib
from thumbor.utils import logger

from wikimedia_thumbor.core.context_importer import ContextImporter
from wikimedia_thumbor.core.importer import Importer


class Extensions:

    extensions = []

    @classmethod
    def load(cls, name):
        '''Load the given extension

        :param name: The extension package name.
        '''

        importlib.import_module(name)

    @classmethod
    def register(cls, extension):
        logger.debug("Loading extension {name}".format(name=extension.name))
        cls.extensions.append(extension)

        for module in extension.modules:
            cls.register_module(**module)

    @classmethod
    def register_module(cls, config_key, class_name, multiple=False):
        ContextImporter.register(config_key.lower())
        Importer.register_module(config_key, class_name, multiple)


class Extension:

    def __init__(self, name):
        '''
        :param name: Extension name.
        '''

        self.name = name
        self.modules = []
        self.handlers = []

    def add_module(self, config_key, class_name, multiple):
        '''Add a module to the extension.

        :param config_key: The module configuration key
        :param class_name: The module class name.
        :param multiple:
        '''

        self.modules.append(dict(
            config_key=config_key,
            class_name=class_name,
            multiple=multiple
        ))

    def add_handler(self, route, handler):
        '''Add a tornado handler to the extension

        :param route: Route of this extension
        :param handler: tornado.web.RequestHandler
        '''

        self.handlers.append((route, handler))
