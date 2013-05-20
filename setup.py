#!/usr/bin/env python

#from distutils.core import setup
from setuptools import setup

setup(
	name='subr',
      version='0.1',
      description='Automagically find subtitles for video files.',
      author='Dominique Dierickx',
      author_email='d.dierickx@gmail.com',
      url='http://github.com/ddierickx/subr.git',
      packages=['subr'],
      install_requires=[
      					'guessit',
      					'requests'
      				   ],
      scripts=['bin/subr']
)
