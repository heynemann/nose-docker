#!/usr/bin/python
# -*- coding: utf-8 -*-

# This file is part of nose-docker.
# https://github.com/heynemann/nose-docker

# Licensed under the MIT license:
# http://www.opensource.org/licenses/MIT-license
# Copyright (c) 2014 Bernardo Heynemann heynemann@gmail.com

import sys
import os
from os.path import abspath
from time import time
from xml.sax import saxutils as su

from lxml.cssselect import CSSSelector
from lxml import etree
import nose.core
from nose.plugins.base import Plugin
from nose.result import TextTestResult
import sh
from sh import docker


FAILURE_SELECTOR = CSSSelector('failure')
ERROR_SELECTOR = CSSSelector('error')


class DockerTestResult(TextTestResult):
    def addFailure(self, test, failure_message):
        self.failures.append((test, failure_message))
        self._mirrorOutput = True


def process_tests(suite, process):
    """Given a nested disaster of [Lazy]Suites, traverse to the first level
    that has setup or teardown, and do something to them.

    If we were to traverse all the way to the leaves (the Tests)
    indiscriminately and return them, when the runner later calls them, they'd
    run without reference to the suite that contained them, so they'd miss
    their class-, module-, and package-wide setup and teardown routines.

    The nested suites form basically a double-linked tree, and suites will call
    up to their containing suites to run their setups and teardowns, but it
    would be hubris to assume that something you saw fit to setup or teardown
    at the module level is less costly to repeat than DB fixtures. Also, those
    sorts of setups and teardowns are extremely rare in our code. Thus, we
    limit the granularity of bucketing to the first level that has setups or
    teardowns.

    :arg process: The thing to call once we get to a leaf or a test with setup
        or teardown

    """
    if (
        not hasattr(suite, '_tests') or
        (hasattr(suite, 'hasFixtures') and suite.hasFixtures())
    ):
        # We hit a Test or something with setup, so do the thing. (Note that
        # "fixtures" here means setup or teardown routines, not Django
        # fixtures.)
        process(suite)
    else:
        for t in suite._tests:
            process_tests(t, process)


class NoseDockerPlugin(Plugin):
    name = "docker"

    #_options = (
        ##("color", "YANC color override - one of on,off [%s]", "store"),
    #)

    #def options(self, parser, env):
        #super(NoseDockerPlugin, self).options(parser, env)
        #for name, help, action in self._options:
            #env_opt = "NOSE_YANC_%s" % name.upper()
            #parser.add_option("--yanc-%s" % name.replace("_", "-"),
                            #action=action,
                            #dest="yanc_%s" % name,
                            #default=env.get(env_opt),
                            #help=help % env_opt)

    #def configure(self, options, conf):
        #super(NoseDockerPlugin, self).configure(options, conf)
        #for name, help, dummy in self._options:
            #name = "yanc_%s" % name
            #setattr(self, name, getattr(options, name))
        #self.color = self.yanc_color != "off" \
            #and (self.yanc_color == "on"
                #or (hasattr(self.conf, "stream")
                    #and hasattr(self.conf.stream, "isatty")
                    #and self.conf.stream.isatty()))

    #def wantMethod(self, method):
        #if method.__name__.startswith('test_'):
            #self.collected_methods.append(method)
            #return True

        #return False

    #def prepareTest(self, suite):
        #flattened = []
        #process_tests(suite, flattened.append)

        #for test_case in flattened:
            #test_module = test_case.context.__module__
            #test_case_name = test_case.context.__name__

            #for test in test_case._tests:
                #test_name = test.test._testMethodName

                #full_name = '%s:%s.%s' % (test_module, test_case_name, test_name)

                ##print docker.run(
                    ##'--rm',
                    ##'-v',
                    ##'%s:/app' % abspath(os.curdir),
                    ##'dockerfile/python',
                    ##'/bin/bash',
                    ##c="cd /app && make setup && echo 'running tests for %s...' && nosetests -sv %s" % (full_name, full_name),
                ##)

                #self.addSuccess(test)

    def prepareTestRunner(self, runner):
        return TestRunner(runner.stream, verbosity=self.conf.verbosity,
                                 config=self.conf)

    def begin(self):
        pass

    def finalize(self, result):
        pass


class TestRunner(nose.core.TextTestRunner):
    def get_test_descriptions(self, suite):
        for test_case in suite:
            for test in test_case._tests:
                yield test.shortDescription().replace('.pyc', '.py')

    def run(self, test):
        descriptions = tuple(self.get_test_descriptions(test))
        flattened = []
        process_tests(test, flattened.append)

        result = DockerTestResult(self.stream, descriptions, self.verbosity, config=self.config)

        startTime = time()

        for test_case in flattened:
            test_module = test_case.context.__module__
            test_case_name = test_case.context.__name__

            for test in test_case._tests:
                test_name = test.test._testMethodName

                full_name = '%s:%s.%s' % (test_module, test_case_name, test_name)

                self.run_test_in_docker(test, full_name, result)

        stopTime = time()
        timeTaken = stopTime - startTime
        if not result.wasSuccessful():
            result.printErrors()

        run = result.testsRun
        self.stream.writeln("Ran %d test%s in %.3fs" %
                            (run, run != 1 and "s" or "", timeTaken))
        self.stream.writeln()

        expectedFails = unexpectedSuccesses = skipped = 0
        try:
            results = map(len, (result.expectedFailures,
                                result.unexpectedSuccesses,
                                result.skipped))
        except AttributeError:
            pass
        else:
            expectedFails, unexpectedSuccesses, skipped = results

        infos = []
        if not result.wasSuccessful():
            self.stream.write("FAILED")
            failed, errored = map(len, (result.failures, result.errors))
            if failed:
                infos.append("failures=%d" % failed)
            if errored:
                infos.append("errors=%d" % errored)
        else:
            self.stream.write("OK")
        if skipped:
            infos.append("skipped=%d" % skipped)
        if expectedFails:
            infos.append("expected failures=%d" % expectedFails)
        if unexpectedSuccesses:
            infos.append("unexpected successes=%d" % unexpectedSuccesses)
        if infos:
            self.stream.writeln(" (%s)" % (", ".join(infos),))
        else:
            self.stream.write("\n")

        return result

    def run_test_in_docker(self, test, full_name, result):
        try:
            exit_with_proper_code = 'EXIT=$?; cat /app/nosetests.xml; exit $EXIT'
            xml = docker.run(
                '--rm',
                '-v',
                '%s:/app' % abspath(os.curdir),
                'dockerfile/python',
                '/bin/bash',
                c="cd /app && make setup && echo 'running tests for %s...' && nosetests --with-xunit %s; %s" % (
                    full_name,
                    full_name,
                    exit_with_proper_code
                ),
            )

            result.addSuccess(test)
        except sh.ErrorReturnCode:
            err = sys.exc_info()[1]
            xml = err.stdout[err.stdout.index('<?xml'):]
            root = etree.fromstring(xml)

            failure = FAILURE_SELECTOR(root)
            if failure:
                failure_message = su.unescape(failure[0].text).replace('\\n', '\n')
                result.addFailure(test, failure_message)

            error = ERROR_SELECTOR(root)
            if error:
                result.addError(test, su.unescape(error[0].text))

        finally:
            result.testsRun += 1
