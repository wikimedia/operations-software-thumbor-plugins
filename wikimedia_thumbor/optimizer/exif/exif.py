#!/usr/bin/python
# -*- coding: utf-8 -*-

# thumbor imaging service
# https://github.com/thumbor/thumbor/wiki

# Licensed under the MIT license:
# http://www.opensource.org/licenses/mit-license
# Copyright (c) 2011 globo.com timehome@corp.globo.com
# Copyright (c) 2015 Wikimedia Foundation

# EXIF optimizer, aims to reduce thumbnail weight as much as possible
# while retaining some critical metadata

import os

from thumbor.optimizers import BaseOptimizer
from thumbor.utils import logger

from wikimedia_thumbor.shell_runner import ShellRunner


class Optimizer(BaseOptimizer):
    def __init__(self, context):
        super(Optimizer, self).__init__(context)

        self.runnable = True
        self.exiftool_path = self.context.config.EXIFTOOL_PATH
        self.exif_fields_to_keep = self.context.config.EXIF_FIELDS_TO_KEEP
        self.tinyrgb_path = self.context.config.EXIF_TINYRGB_PATH
        self.tinyrgb_icc_replace = self.context.config.EXIF_TINYRGB_ICC_REPLACE

        if not (os.path.isfile(self.exiftool_path)
                and os.access(self.exiftool_path, os.X_OK)):
            logger.error(
                "ERROR exiftool path '{0}' is not accessible"
                .format(self.exiftool_path)
            )
            self.runnable = False

        if not (os.path.isfile(self.tinyrgb_path)
                and os.access(self.tinyrgb_path, os.R_OK)):
            logger.error(
                "ERROR tinyrgb path '{0}' is not accessible"
                .format(self.tinyrgb_path)
            )
            self.tinyrgb_path = False

    def should_run(self, image_extension, buffer):
        if image_extension is None:
            return False

        good_extension = 'jpg' in image_extension or 'jpeg' in image_extension
        return good_extension and self.runnable

    def optimize(self, buffer, input_file, output_file):
        exif_fields = self.exif_fields_to_keep

        # TinyRGB is a lightweight sRGB swap-in replacement created by Facebook
        # If the image is sRGB, swap the existing heavy profile for TinyRGB
        # Only works if icc_profile is configured to be preserved in
        # EXIF_FIELDS_TO_KEEP
        if (self.tinyrgb_path):
            command = [
                self.exiftool_path,
                '-DeviceModelDesc',
                '-S',
                '-T',
                input_file
            ]

            code, stderr, stdout = ShellRunner.command(command, self.context)

            if (stdout.rstrip().lower() == self.tinyrgb_icc_replace.lower()):
                new_icc = 'icc_profile<=%s' % (
                    self.tinyrgb_path
                )
                exif_fields = [
                    new_icc if i == 'icc_profile' else i for i in exif_fields
                ]

        # Strip all EXIF fields except the ones we want to
        # explicitely copy over
        command = [
            self.exiftool_path,
            input_file,
            '-all=',
            '-tagsFromFile',
            '@'
        ]
        command += ['-{0}'.format(i) for i in exif_fields]
        command += [
            '-m',
            '-o',
            output_file
        ]

        # exiftool can't overwrite files, and thumbor has already created it
        os.remove(output_file)
        ShellRunner.command(command, self.context)
