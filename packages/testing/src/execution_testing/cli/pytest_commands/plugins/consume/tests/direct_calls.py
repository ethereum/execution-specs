"""Call a pytest fixture's function directly, outside a pytest session."""

from typing import Any, Callable


def fixture_body(fixture: Any) -> Callable[..., Any]:
    """Return the function `@pytest.fixture` wrapped."""
    body: Callable[..., Any] = fixture.__wrapped__
    return body
