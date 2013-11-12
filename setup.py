#!/usr/bin/env python

from distutils.core import setup

# FIXME: We will stick this shit here for now for the sake of running Travis CI.
__author__ = 'Sumin Byeon'
__email__ = 'suminb@gmail.com'
__version__ = '0.2.16'

#from hallucination import __version__, __author__, __email__


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
      version=__version__,
      description='A Python library for proxy server list management',
      long_description=readme(),
      author=__author__,
      author_email=__email__,
      url='http://github.com/suminb/hallucination',
      packages=['hallucination'],
      requires=[
          'sqlalchemy (>= 0.8)',
          'requests (>= 2.0.0)',
      ],
    )
