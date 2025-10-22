import urllib3
from typing import Tuple, Mapping
from _typeshed import Incomplete
from requests.adapters import HTTPAdapter
from requests.models import PreparedRequest
from urllib3.util import Timeout
from urllib3.connectionpool import HTTPConnectionPool
from urllib3._collections import RecentlyUsedContainer
from socket import socket

class UnixHTTPConnection(urllib3.connection.HTTPConnection):
    unix_socket_url: str
    timeout: float | None
    sock: None | socket
    def __init__(
        self, unix_socket_url: str, timeout: float | None = 60
    ) -> None: ...
    def __del__(self) -> None: ...
    def connect(self) -> None: ...

class UnixHTTPConnectionPool(urllib3.connectionpool.HTTPConnectionPool):
    socket_path: str
    timeout: Timeout
    def __init__(
        self, socket_path: str, timeout: float | None = 60
    ) -> None: ...

class UnixAdapter(HTTPAdapter):
    timeout: float | None
    pools: RecentlyUsedContainer
    def __init__(
        self,
        timeout: float | None = 60,
        pool_connections: int = 25,
        *args: Incomplete,
        **kwargs: Incomplete,
    ) -> None: ...
    def get_connection_with_tls_context(
        self,
        request: PreparedRequest,
        verify: bool | str | None,
        proxies: Mapping[str, str] | None = None,
        cert: str | Tuple[str, str] | None = None,
    ) -> HTTPConnectionPool: ...
    def get_connection(
        self, url: str | bytes, proxies: Mapping[str, str] | None = None
    ) -> HTTPConnectionPool: ...
    def request_url(
        self, request: PreparedRequest, proxies: Mapping[str, str] | None
    ) -> str: ...
    def close(self) -> None: ...
