Configuration
-------------

(TODO: Fill out this section)

Usage
-----

Python invocation
`````````````````

To import a text file containing a proxy server list:

.. code-block:: python

    proxy_factory = ProxyFactory(config=dict(db_uri='sqlite:///test.db'))
    proxy_factory.import_proxies('proxylist.txt')

To make a request:

.. code-block:: python

    r = proxy_factory.make_request('https://github.com/suminb/hallucination')
    print r.text

Shell frontend
``````````````

To create an SQLite database file:

.. code-block:: console

    python frontend.py -c proxy.db

To export the proxy server list to a text file:

.. code-block:: console

    python frontend.py -e proxylist.txt

To import a text file containing a proxy server list:

.. code-block:: console

    python frontend.py -i proxylist.txt
