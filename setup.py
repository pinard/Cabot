#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright © 2004 PROGICIELS Bourbeau-Pinard, inc. Montréal.
# François Pinard <pinard@progiciels-bpi.ca>, 2004.

from distutils.core import setup

setup(name='Cabot',
      version='0.0',
      description="IRC bot for `icule'.",
      author='François Pinard',
      author_email='pinard@iro.umontreal.ca',
      url='http://www.iro.umontreal.ca/~pinard',
      scripts=['cabot'],
      packages=['Cabot'])

