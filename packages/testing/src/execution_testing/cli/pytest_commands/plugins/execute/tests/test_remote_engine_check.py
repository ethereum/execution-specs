"""
Test that `execute remote` checks the engine endpoint before the session.

The tests run against a local HTTP server that authenticates the engine
API the way execution clients do: requests whose JWT is not signed with the
expected secret are rejected with `401 Unauthorized` before the JSON-RPC
method is dispatched.
"""

import json
import logging
import threading
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Generator
from unittest.mock import patch

import jwt
import pytest

from execution_testing.rpc import EngineRPC
from execution_testing.test_types.chain_config_types import (
    ChainConfigDefaults,
)

from ..rpc.remote import pytest_configure, verify_engine_endpoint

JWT_SECRET = b"secretsecretsecretsecretsecretse"

CLIENT_VERSION = {
    "code": "GE",
    "name": "go-ethereum",
    "version": "1.16.0",
    "commit": "0xfa4ff922",
}


class EngineServer(ThreadingHTTPServer):
    """Local JSON-RPC server with a JWT-authenticated engine API."""

    # JSON-RPC responses by method name, or a JSON-RPC error if missing.
    results: Dict[str, Any]
    # HTTP status to answer authenticated requests with, if not 200 OK.
    status: HTTPStatus = HTTPStatus.OK

    @property
    def url(self) -> str:
        """Return the URL the server listens on."""
        host, port = self.server_address[:2]
        return f"http://{host!s}:{port}"


class EngineHandler(BaseHTTPRequestHandler):
    """Answer JSON-RPC requests, authenticating the `engine_` namespace."""

    server: EngineServer

    def do_POST(self) -> None:
        """Answer one JSON-RPC request."""
        length = int(self.headers["Content-Length"])
        request = json.loads(self.rfile.read(length))
        method = request["method"]
        if method.startswith("engine_") and not self.authenticated():
            self.send_error(HTTPStatus.UNAUTHORIZED, "invalid token")
            return
        if self.server.status != HTTPStatus.OK:
            self.send_error(self.server.status)
            return
        response: Dict[str, Any] = {"jsonrpc": "2.0", "id": request["id"]}
        if method in self.server.results:
            response["result"] = self.server.results[method]
        else:
            response["error"] = {
                "code": -32601,
                "message": f"the method {method} does not exist",
            }
        body = json.dumps(response).encode()
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def authenticated(self) -> bool:
        """Return whether the request carries a JWT signed by the secret."""
        authorization = self.headers.get("Authorization", "")
        token = authorization.removeprefix("Bearer ")
        try:
            jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        except jwt.InvalidTokenError:
            return False
        return True

    def log_message(self, *args: Any) -> None:
        """Keep the test output free of access logs."""
        del args


@pytest.fixture
def engine_server() -> Generator[EngineServer, None, None]:
    """Serve the engine API on a free local port for the test."""
    server = EngineServer(("127.0.0.1", 0), EngineHandler)
    server.results = {
        "eth_chainId": hex(ChainConfigDefaults.chain_id),
        "engine_getClientVersionV1": [CLIENT_VERSION],
    }
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield server
    server.shutdown()
    server.server_close()
    thread.join()


def test_valid_jwt_secret(
    engine_server: EngineServer, caplog: pytest.LogCaptureFixture
) -> None:
    """The check passes and logs the client behind the engine endpoint."""
    engine_rpc = EngineRPC(engine_server.url, jwt_secret=JWT_SECRET)
    with caplog.at_level(logging.INFO):
        verify_engine_endpoint(engine_rpc)
    assert "go-ethereum 1.16.0 (GE, 0xfa4ff922)" in caplog.text


def test_invalid_jwt_secret(engine_server: EngineServer) -> None:
    """A JWT secret that the engine endpoint rejects ends the session."""
    engine_rpc = EngineRPC(engine_server.url, jwt_secret=b"wrong secret")
    with pytest.raises(pytest.exit.Exception, match="rejected the JWT secret"):
        verify_engine_endpoint(engine_rpc)


@pytest.mark.parametrize(
    "result",
    [None, [{"code": "GE"}]],
    ids=["method_not_found", "malformed_response"],
)
def test_client_version_not_reported(
    engine_server: EngineServer,
    caplog: pytest.LogCaptureFixture,
    result: Any,
) -> None:
    """
    The check passes if the client authenticates the request but does not
    report a valid client version.
    """
    if result is None:
        del engine_server.results["engine_getClientVersionV1"]
    else:
        engine_server.results["engine_getClientVersionV1"] = result
    engine_rpc = EngineRPC(engine_server.url, jwt_secret=JWT_SECRET)
    verify_engine_endpoint(engine_rpc)
    assert "did not report its client version" in caplog.text


def test_engine_endpoint_http_error(engine_server: EngineServer) -> None:
    """An engine endpoint answering with an HTTP error ends the session."""
    engine_server.status = HTTPStatus.NOT_FOUND
    engine_rpc = EngineRPC(engine_server.url, jwt_secret=JWT_SECRET)
    with pytest.raises(pytest.exit.Exception, match="returned an error"):
        verify_engine_endpoint(engine_rpc)


def test_engine_endpoint_unreachable(engine_server: EngineServer) -> None:
    """An engine endpoint that cannot be reached ends the session."""
    url = engine_server.url
    engine_server.shutdown()
    engine_server.server_close()
    engine_rpc = EngineRPC(url, jwt_secret=JWT_SECRET)
    with (
        patch("time.sleep"),
        pytest.raises(pytest.exit.Exception, match="Unable to reach"),
    ):
        verify_engine_endpoint(engine_rpc)


class RemoteConfig:
    """Minimal config object for exercising remote plugin setup."""

    engine_rpc: EngineRPC | None

    def __init__(self, url: str, jwt_secret: str) -> None:
        self.options = {
            "rpc_endpoint": url,
            "engine_endpoint": url,
            "engine_jwt_secret": jwt_secret,
            "engine_jwt_secret_file": None,
        }

    def getoption(self, name: str, default: Any = None) -> Any:
        """Return configured option values used by pytest_configure."""
        return self.options.get(name, default)


@pytest.mark.parametrize(
    "jwt_secret,accepted",
    [
        pytest.param(JWT_SECRET.decode(), True, id="valid_secret"),
        pytest.param("wrong secret", False, id="invalid_secret"),
    ],
)
def test_pytest_configure_checks_jwt_secret(
    engine_server: EngineServer, jwt_secret: str, accepted: bool
) -> None:
    """`pytest_configure` checks the JWT secret given on the command line."""
    config = RemoteConfig(engine_server.url, jwt_secret)
    with patch(
        "execution_testing.cli.pytest_commands.plugins.execute.rpc.remote."
        "is_help_or_collectonly_mode",
        return_value=False,
    ):
        if accepted:
            pytest_configure(config)  # type: ignore[arg-type]
            assert config.engine_rpc is not None
        else:
            with pytest.raises(
                pytest.exit.Exception, match="rejected the JWT secret"
            ):
                pytest_configure(config)  # type: ignore[arg-type]
