#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of nose-docker.
# https://github.com/heynemann/nose-docker

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Bernardo Heynemann heynemann@gmail.com

import yaml
import os.path
import hashlib


class TestConfig(object):
    def __init__(self, build_commands, base_image='dockerfile/python', watched_files=None):
        self.build_commands = build_commands
        self.base_image = base_image
        self.watched_files = watched_files
        if self.watched_files is None:
            self.watched_files = [
                'Makefile',
                'setup.py',
                'requirements.txt'
            ]

    def get_container_tag(self):
        contents = []
        for filename in self.watched_files:
            if not os.path.isabs(filename):
                filename = os.path.abspath(filename)
            if not os.path.exists(filename):
                continue
            with open(filename) as f:
                contents.append(f.read())

        result = "".join(contents)

        return hashlib.sha512(result).hexdigest()

    @classmethod
    def load(cls):
        yml_path = os.path.abspath('./.nose-docker.yaml')
        if not os.path.exists(yml_path):
            return None

        with open(yml_path) as yml:
            contents = yml.read()

        data = yaml.load(contents)
        build_commands = data.get('build', None)
        if build_commands is None:
            return None

        if not isinstance(build_commands, (tuple, set, list)):
            build_commands = [build_commands]

        base_image = data.get('base_image', 'dockerfile/python')
        watched_files = data.get('watched', None)

        return cls(
            build_commands=build_commands, base_image=base_image, watched_files=watched_files
        )
