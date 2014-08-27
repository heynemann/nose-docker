#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of nose-docker.
# https://github.com/heynemann/nose-docker

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Bernardo Heynemann heynemann@gmail.com

import os
from os.path import abspath

from nose.plugins import Plugin
from sh import docker


class NoseDockerPlugin(Plugin):
    name = "docker"

    _options = (
        #("color", "YANC color override - one of on,off [%s]", "store"),
    )

    def options(self, parser, env):
        super(NoseDockerPlugin, self).options(parser, env)
        #for name, help, action in self._options:
            #env_opt = "NOSE_YANC_%s" % name.upper()
            #parser.add_option("--yanc-%s" % name.replace("_", "-"),
                            #action=action,
                            #dest="yanc_%s" % name,
                            #default=env.get(env_opt),
                            #help=help % env_opt)

    def configure(self, options, conf):
        super(NoseDockerPlugin, self).configure(options, conf)
        #for name, help, dummy in self._options:
            #name = "yanc_%s" % name
            #setattr(self, name, getattr(options, name))
        #self.color = self.yanc_color != "off" \
            #and (self.yanc_color == "on"
                #or (hasattr(self.conf, "stream")
                    #and hasattr(self.conf.stream, "isatty")
                    #and self.conf.stream.isatty()))

    def wantMethod(self, method):
        if method.__name__.startswith('test_'):
            self.collected_methods.append(method)

        return False

    def prepareTest(self, suite):
        for test in self.collected_methods:
            test_case = test.im_class
            test_module = test_case.__module__
            test_name = test.__name__
            command = 'run --rm -v %s:/app dockerfile/python /bin/bash -c \'cd /app && make setup && nosetests -sv %s:%s.%s\'' % (
                abspath(os.curdir),
                test_module,
                test_case.__name__,
                test_name
            )

            print docker(command.split())

    def begin(self):
        self.collected_methods = []
        #try:
            #result = docker.run('ubuntu:14.04', '/bin/echo', '"hello world"')
        #except ErrorReturnCode:
            #exit(1)

    def finalize(self, result):
        pass

