"""Test suite for test spec submodules of the `ethereum_test` module."""

from typing import Type

import pytest

from ethereum_test_base_types import Account
from ethereum_test_types import Alloc


@pytest.fixture()
def post(request: pytest.FixtureRequest) -> Alloc:
    """Post state: Set from the test's indirectly parametrized `post` parameter."""
    return Alloc.model_validate(request.param)


@pytest.fixture()
def alloc(request: pytest.FixtureRequest) -> Alloc:
    """Alloc state: Set from the test's indirectly parametrized `alloc` parameter."""
    return Alloc.model_validate(request.param)


@pytest.mark.parametrize(
    ["post", "alloc", "expected_exception_type"],
    [
        # Account should not exist but contained in alloc
        (
            {"0x0": Account.NONEXISTENT},
            {
                "0x00": {
                    "nonce": "1",
                    "code": "0x123",
                    "balance": "1",
                    "storage": {0: 1},
                }
            },
            Alloc.UnexpectedAccountError,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x00": Account.NONEXISTENT},
            {"0x0": {"nonce": "1"}},
            Alloc.UnexpectedAccountError,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x1": Account.NONEXISTENT},
            {"0x01": {"balance": "1"}},
            Alloc.UnexpectedAccountError,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x0a": Account.NONEXISTENT},
            {"0x0A": {"code": "0x00"}},
            Alloc.UnexpectedAccountError,
        ),
        # Account should exist but not in alloc
        (
            {"0x0A": Account()},
            {
                "0x0B": {
                    "nonce": "1",
                    "code": "0x123",
                    "balance": "1",
                    "storage": {0: 1},
                }
            },
            Alloc.MissingAccountError,
        ),
        # Account should exist and contained in alloc, but don't care about
        # values
        (
            {"0x1": Account()},
            {
                "0x1": {
                    "nonce": "1",
                    "code": "0x123",
                    "balance": "1",
                    "storage": {0: 1},
                }
            },
            None,
        ),
        # Account should exist and contained in alloc, single incorrect value
        (
            {"0x1": Account(nonce=0)},
            {
                "0x1": {
                    "nonce": "1",
                    "code": "0x123",
                    "balance": "1",
                    "storage": {0: 1},
                }
            },
            Account.NonceMismatchError,
        ),
    ],
    indirect=["post", "alloc"],
)
def test_verify_post_alloc(
    post: Alloc, alloc: Alloc, expected_exception_type: Type[Exception] | None
):
    """Test `verify_post_alloc` method of `Alloc`."""
    if expected_exception_type is None:
        post.verify_post_alloc(alloc)
    else:
        with pytest.raises(expected_exception_type) as _:
            post.verify_post_alloc(alloc)
