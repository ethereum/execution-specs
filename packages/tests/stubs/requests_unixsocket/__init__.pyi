import requests
from typing import Tuple, Callable, Self
from requests.sessions import _Data
from _typeshed import Incomplete
from requests.models import _JSON, Response

DEFAULT_SCHEME: str

class Session(requests.Session):
    def __init__(
        self, url_scheme: str = ..., *args: Incomplete, **kwargs: Incomplete
    ) -> None: ...

class monkeypatch:
    session: Session
    methods: Tuple[str | bytes, ...]
    orig_methods: dict[str | bytes, Callable]
    def __init__(self, url_scheme: str = ...) -> None: ...
    def __enter__(self) -> Self: ...
    def __exit__(self, *args: Incomplete) -> None: ...

def request(
    method: str | bytes, url: str | bytes, **kwargs: Incomplete
) -> Response: ...
def get(url: str | bytes, **kwargs: Incomplete) -> Response: ...
def head(url: str | bytes, **kwargs: Incomplete) -> Response: ...
def post(
    url: str | bytes,
    data: _Data | None = None,
    json: _JSON | None = None,
    **kwargs: Incomplete,
) -> Response: ...
def patch(
    url: str | bytes, data: _Data | None = None, **kwargs: Incomplete
) -> Response: ...
def put(
    url: str | bytes, data: _Data | None = None, **kwargs: Incomplete
) -> Response: ...
def delete(url: str | bytes, **kwargs: Incomplete) -> Response: ...
def options(url: str | bytes, **kwargs: Incomplete) -> Response: ...
