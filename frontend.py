import json
from queue import Queue
import sys
from threading import Thread

import click
import logging

from hallucination import ProxyFactory


logger = logging.getLogger("hallucination")
logger.addHandler(logging.StreamHandler(sys.stdout))
logger.setLevel(logging.INFO)

config = {}

# FIXME: This is not a good design
url = "{protocol}://translate.google.com"
proxy_factory = None

threads = 8


class TestrunThread(Thread):
    def __init__(self, queue, config):
        super(TestrunThread, self).__init__()

        self.queue = queue

        self.proxy_factory = ProxyFactory(
            config=dict(db_uri=config["db_uri"]), logger=logger
        )

    def run(self):
        while True:
            logger.info("Qsize = {} (approx.)".format(self.queue.qsize()))

            url, proxy = self.queue.get()

            logger.info("Test run: Fetching %s via %s" % (url, proxy))
            self.proxy_factory.make_request(url, proxy=proxy, timeout=10)

            self.queue.task_done()


@click.group()
def cli():
    # FIXME: Temporary workaround
    with open("config.json") as fin:
        global config
        config = json.loads(fin.read())

    global proxy_factory
    proxy_factory = ProxyFactory(
        config=dict(db_uri=config["db_uri"]), logger=logger
    )


@cli.command()
def create():
    proxy_factory.create_db()


@cli.command()
@click.argument("input_file", type=click.File("r"))
def import_list(input_file):
    """Imports a list of proxy servers from a text file."""
    proxy_factory.import_proxies(input_file)


@cli.command()
@click.argument("output_file", type=click.File("w"))
def export_list(output_file):
    """Exports the list of proxy servers to the standard output."""
    proxy_factory.export_proxies(output_file)


@cli.command()
@click.argument("n", default=1)
@click.argument("protocols", nargs=-1)
def select(n, protocols):
    if not protocols:
        # Provide some reasonable default value
        protocols = ["http", "https"]

    for row in proxy_factory.select(n=n, protocols=protocols):
        print(row)


@cli.command()
def evaluate():
    """
    Selects proxy servers that have not been recently evaluated, and evaluates
    each of them.

    Refered http://docs.python.org/2/library/queue.html for skeleton code.
    """

    queue = Queue()

    for i in range(threads):
        thread = TestrunThread(queue=queue, config=config)
        thread.daemon = True
        thread.start()

    for proxy in proxy_factory.get_evaluation_targets():
        queue.put((url.format(protocol=proxy.protocol), proxy))

    queue.join()


if __name__ == "__main__":
    cli()
