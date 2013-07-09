Configuration
-----

(TODO: Fill out this section)

Usage
-----

### Python invocation

To import a text file containing a proxy server list:

    import_proxies('proxylist.txt')

To make a request:

    r = make_request('https://github.com/suminb/hallucination')
    print r.text

### Shell frontend

To create an SQLite database file:

    python frontend.py -c proxy.db

To export the proxy server list to a text file:

    python frontend.py -e proxylist.txt

To import a text file containing a proxy server list:

    python frontend.py -i proxylist.txt

