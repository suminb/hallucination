Prerequisites
-------------

- `python-requests <http://docs.python-requests.org/en/latest/>`_
- SQLAlchemy_

.. _SQLAlchemy: http://www.sqlalchemy.org/

Usage
-----

Python invocation
`````````````````

To create database tables:

.. code-block:: python

    proxy_factory = ProxyFactory(config=dict(db_uri='sqlite:///test.db'))
    proxy_factory.create_db()

To import a text file containing a proxy server list:

.. code-block:: python

    proxy_factory = ProxyFactory(config=dict(db_uri='sqlite:///test.db'))
    proxy_factory.import_proxies('proxylist.txt')

Hallucination supports multiple database backends, as long as supported by SQLAlchemy_.

.. code-block:: python

    proxy_factory = ProxyFactory(config=dict(db_uri='postgres://user:password@host/database'))

To make a request:

.. code-block:: python

    r = proxy_factory.make_request('http://github.com/suminb/hallucination')
    print r.text

You may specify timeout in seconds:

.. code-block:: python

    r = proxy_factory.make_request('http://github.com/suminb/hallucination', timeout=5)
    print r.text


Shell frontend
``````````````

To create an SQLite database file:

.. code-block:: console

    python frontend.py -d proxy.db -c

To import a text file containing a proxy server list:

.. code-block:: console

    python frontend.py -d proxy.db -i proxylist.txt


To export the proxy server list to a text file:

.. code-block:: console

    python frontend.py -d proxy.db -x proxylist.txt

An exported file may look like the following:

.. code-block:: text

    http://84.42.3.3:3128
    http://77.94.48.5:80
    http://209.62.12.130:8118
    http://159.255.160.23:8080
    http://50.57.170.105:80
