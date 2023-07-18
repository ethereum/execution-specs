"""
Test suite for test spec submodules of the `ethereum_test` module.
"""

from typing import Any, Mapping

import pytest

from ..common import Account
from ..spec import verify_post_alloc


@pytest.mark.parametrize(
    ["post", "alloc", "should_pass"],
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
            False,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x00": Account.NONEXISTENT},
            {"0x0": {"nonce": "1"}},
            False,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x1": Account.NONEXISTENT},
            {"0x01": {"balance": "1"}},
            False,
        ),
        # Account should not exist but contained in alloc
        (
            {"0x0a": Account.NONEXISTENT},
            {"0x0A": {"code": "0x00"}},
            False,
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
            False,
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
            True,
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
            False,
        ),
    ],
)
def test_verify_post_alloc(
    post: Mapping[str, Account], alloc: Mapping[str, Any], should_pass: bool
):
    if should_pass:
        verify_post_alloc(post, alloc)
    else:
        with pytest.raises(Exception) as _:
            verify_post_alloc(post, alloc)
