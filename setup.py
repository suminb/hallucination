#!/usr/bin/env python

from distutils.core import setup
import hallucination


def readme():
    try:
        f = open('README.rst')
        content = f.read()
        f.close()
        return content
    except IOError:
        pass
    except OSError:
        pass


setup(name='hallucination',
      version=hallucination.__version__,
      description='A Python library for proxy server list management',
      long_description=readme(),
      author=hallucination.__author__,
      author_email=hallucination.__email__,
      url='http://github.com/suminb/hallucination',
      packages=['hallucination'],
      requires=[
          'sqlalchemy (>= 0.8)',
          'requests (>= 2.0.0)',
      ],
    )
