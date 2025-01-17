"""
Run ethereum-spec-evm as a daemon.
"""

import argparse
import json
import os.path
import socketserver
import time
from http.server import BaseHTTPRequestHandler
from io import StringIO, TextIOWrapper
from socket import socket
from threading import Thread
from typing import Any, Tuple, Union
from urllib.parse import parse_qs, urlparse


def daemon_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the daemon tool subparser.
    """
    parser = subparsers.add_parser("daemon", help="Spawn t8n as a daemon")
    parser.add_argument("--uds", help="Unix domain socket path")
    parser.add_argument(
        "--timeout",
        help="Timeout to shutdown daemon if there are not requests"
        " (0 for no timeout)",
        type=int,
    )


class _EvmToolHandler(BaseHTTPRequestHandler):
    def log_request(
        self, code: int | str = "-", size: int | str = "-"
    ) -> None:
        """Don't log requests"""
        pass

    def do_POST(self) -> None:
        from . import main

        content_length = int(self.headers["Content-Length"])
        content_bytes = self.rfile.read(content_length)
        content = json.loads(content_bytes)

        input_string = json.dumps(content["input"])
        input = StringIO(input_string)

        args = [
            "t8n",
            "--input.env=stdin",
            "--input.alloc=stdin",
            "--input.txs=stdin",
            "--output.result=stdout",
            "--output.body=stdout",
            "--output.alloc=stdout",
            f"--state.fork={content['state']['fork']}",
            f"--state.chainid={content['state']['chainid']}",
            f"--state.reward={content['state']['reward']}",
        ]

        query_string = urlparse(self.path).query
        if query_string:
            query = parse_qs(
                query_string,
                keep_blank_values=True,
                strict_parsing=True,
                errors="strict",
            )
            args += query.get("arg", [])

        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        self.end_headers()

        # `self.wfile` is missing the `name` attribute so it doesn't strictly
        # satisfy the bounds for `TextIOWrapper`. Fortunately nothing uses
        # `name` so far, so we can safely ignore the error.
        with TextIOWrapper(
            self.wfile, encoding="utf-8"  # type: ignore[type-var]
        ) as out_wrapper:
            main(args=args, out_file=out_wrapper, in_file=input)


class _UnixSocketHttpServer(socketserver.UnixStreamServer):
    last_response: float
    shutdown_timeout: int

    def __init__(
        self, *args: Any, shutdown_timeout: int, **kwargs: Any
    ) -> None:
        self.shutdown_timeout = shutdown_timeout
        # Add a 60-second allowance to prevent server from timing out during
        # startup
        self.last_response = time.monotonic() + 60.0
        super().__init__(*args, **kwargs)

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
        while self.shutdown_timeout != 0:
            time.sleep(11.0)
            now = time.monotonic()
            last_response = self.last_response
            if last_response is None:
                self.last_response = now
            elif now - last_response > float(self.shutdown_timeout):
                self.shutdown()
                break


class Daemon:
    """
    Converts HTTP requests into ethereum-spec-evm calls.
    """

    def __init__(self, options: argparse.Namespace) -> None:
        if options.uds is None:
            try:
                from platformdirs import user_runtime_dir
            except ImportError as e:
                raise Exception(
                    "Missing plaformdirs dependency (try installing "
                    "ethereum[tools] extra)"
                ) from e
            runtime_dir = user_runtime_dir(
                appname="ethereum-spec-evm",
                appauthor="org.ethereum",
                ensure_exists=True,
            )
            self.uds = os.path.join(runtime_dir, "daemon.sock")
        else:
            self.uds = options.uds

        self.timeout = options.timeout

    def _run(self) -> int:
        try:
            os.remove(self.uds)
        except IOError:
            pass

        with _UnixSocketHttpServer(
            (self.uds), _EvmToolHandler, shutdown_timeout=self.timeout
        ) as server:
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
