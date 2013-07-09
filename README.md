Usage
-----

### Python invocation

    r = make_request('https://github.com/suminb/hallucination')
    print r.text

### Shell frontend

To export the proxy server list to a text file:

    python frontend.py -e proxylist.txt

To import a text file containing a proxy server list:

    python frontend.py -i proxylist.txt

