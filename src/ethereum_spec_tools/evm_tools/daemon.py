"""
Run ethereum-spec-evm as a daemon.
"""

import argparse
import os.path
import shlex
import socketserver
import time
from http.server import BaseHTTPRequestHandler
from io import StringIO, TextIOWrapper
from socket import socket
from threading import Thread
from typing import Any, Optional, Tuple, Union
from urllib.parse import parse_qs, urlparse

from platformdirs import user_runtime_dir


def daemon_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the daemon tool subparser.
    """
    parser = subparsers.add_parser("daemon", help="Spawn t8n as a daemon")
    parser.add_argument("--uds", help="Unix domain socket path")


class _EvmToolHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        from . import main

        content_length = int(self.headers["Content-Length"])
        content_text = self.rfile.read(content_length).decode("utf-8")
        content = StringIO(content_text)

        query = parse_qs(urlparse(self.path).query, keep_blank_values=True)
        args = shlex.split(query["args"][-1])

        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()

        out_wrapper = TextIOWrapper(self.wfile, encoding="utf-8")
        main(args=args, out_file=out_wrapper, in_file=content)
        out_wrapper.flush()


class _UnixSocketHttpServer(socketserver.UnixStreamServer):
    last_response: Optional[float] = None

    def get_request(self) -> Tuple[Any, Any]:
        request, client_address = super().get_request()
        return (request, ["local", 0])

    def finish_request(
        self, request: Union[socket, Tuple[bytes, socket]], client_address: Any
    ) -> None:
        try:
            super().finish_request(request, client_address)
        finally:
            self.last_response = time.monotonic()

    def check_timeout(self) -> None:
        while True:
            time.sleep(11.0)
            now = time.monotonic()
            last_response = self.last_response
            if last_response is None:
                self.last_response = now
            elif now - last_response > 60.0:
                self.shutdown()
                break


class Daemon:
    """
    Converts HTTP requests into ethereum-spec-evm calls.
    """

    def __init__(self, options: argparse.Namespace) -> None:
        if options.uds is None:
            runtime_dir = user_runtime_dir(
                appname="ethereum-spec-evm",
                appauthor="org.ethereum",
                ensure_exists=True,
            )
            self.uds = os.path.join(runtime_dir, "daemon.sock")
        else:
            self.uds = options.uds

    def _run(self) -> int:
        try:
            os.remove(self.uds)
        except IOError:
            pass

        with _UnixSocketHttpServer((self.uds), _EvmToolHandler) as server:
            server.timeout = 7.0
            timer = Thread(target=server.check_timeout, daemon=True)
            timer.start()

            server.serve_forever()

        return 0

    def run(self) -> int:
        """
        Execute the tool.
        """
        return self._run()
