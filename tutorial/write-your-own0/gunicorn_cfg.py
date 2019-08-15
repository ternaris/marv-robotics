"""Gunicorn configuration for MARV."""

import multiprocessing
import pathlib

# pylint: disable=invalid-name

bind = ':8000'
proc_name = 'marvweb'
raw_env = {
    f'MARV_CONFIG={pathlib.Path(__file__).parent.resolve() / "marv.conf"}',
}
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'aiohttp.GunicornUVLoopWebWorker'
