"""
Test_ext_code_copy_tests_paris.

Ported from:
state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
def test_ext_code_copy_tests_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """EXTCODECOPY from absent, balance-only, empty and code accounts."""
    sender = pre.fund_eoa()
    absent = pre.nonexistent_account()
    balance_only = pre.fund_eoa(amount=10)
    empty_with_nonce = pre.deploy_contract(code=b"")
    source_code = bytes.fromhex(
        "1122334455667788991011121314151617181920212223242526272829303132"
    )
    with_code = pre.deploy_contract(code=source_code)
    memory_fill = 2**256 - 1

    copies = [
        (2, absent, 2, b""),
        (3, balance_only, 2, b""),
        (4, empty_with_nonce, 2, b""),
        (5, with_code, 2, source_code),
        (6, with_code, 200, source_code),
    ]
    code = Bytecode()
    storage = {}
    for slot, address, size, account_code in copies:
        code += (
            Op.MSTORE(offset=0, value=memory_fill)
            + Op.EXTCODECOPY(
                address=address, dest_offset=0x1, offset=0xA, size=size
            )
            + Op.SSTORE(key=slot, value=Op.MLOAD(offset=0x0))
        )
        copied = account_code[0xA : 0xA + size].ljust(size, b"\0")
        word = bytearray(memory_fill.to_bytes(32, "big"))
        word[1 : 1 + size] = copied[:31]
        storage[slot] = int.from_bytes(word[:32], "big")
    contract = pre.deploy_contract(code=code + Op.STOP)

    tx = Transaction(sender=sender, to=contract)

    post = {
        contract: Account(storage=storage),
        absent: Account.NONEXISTENT,
        balance_only: Account(balance=10),
        empty_with_nonce: Account(nonce=1, code=b""),
    }

    state_test(pre=pre, post=post, tx=tx)
