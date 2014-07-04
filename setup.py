#!/usr/bin/env python

try:
    from setuptools import setup
except:
    from distutils.core import setup


setup(name='tinyc',
      version='0.1',
      description='tinyc compiler',
      author='Yusuke Miyazaki',
      author_email='miyazaki.dev@gmail.com',
      url='https://github.com/litesystems/tinyc',
      packages=['tinyc'],
      scripts=['scripts/tinyc'],
      test_suite='tests',
      install_requires=[
          'ply==3.4',
          'enum34==1.0'
      ],
      classifiers=[
          'Development Status :: 3 - Alpha',
          'Environment :: Console',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS',
          'Operating System :: POSIX',
          'Operating System :: Unix',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 2.7',
      ])
