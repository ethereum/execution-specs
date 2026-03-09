"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCodeCopyTest/ExtCodeCopyTestsParisFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ext_code_copy_tests_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )
    callee = Address("0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b")
    callee_1 = Address("0xdddf5374fce5edbc8e2a8697c15331677e6ebf0b")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { (EXTCODECOPY 0xbbbf5374fce5edbc8e2a8697c15331677e6ebf0b 1 10 2) [[2]] (MLOAD 0) (EXTCODECOPY 0xcccf5374fce5edbc8e2a8697c15331677e6ebf0b 1 10 2) [[3]] (MLOAD 0) (EXTCODECOPY 0xdddf5374fce5edbc8e2a8697c15331677e6ebf0b 1 10 2) [[4]] (MLOAD 0) (EXTCODECOPY 0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b 1 10 2) [[5]] (MLOAD 0) (EXTCODECOPY 0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b 1 10 200) [[6]] (MLOAD 0)}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.EXTCODECOPY(
                address=0xBBBF5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                dest_offset=0x1,
                offset=0xA,
                size=0x2,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.EXTCODECOPY(
                address=0xCCCF5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                dest_offset=0x1,
                offset=0xA,
                size=0x2,
            )
            + Op.SSTORE(key=0x3, value=Op.MLOAD(offset=0x0))
            + Op.EXTCODECOPY(
                address=0xDDDF5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                dest_offset=0x1,
                offset=0xA,
                size=0x2,
            )
            + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x0))
            + Op.EXTCODECOPY(
                address=0xEEEF5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                dest_offset=0x1,
                offset=0xA,
                size=0x2,
            )
            + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0x0))
            + Op.EXTCODECOPY(
                address=0xEEEF5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                dest_offset=0x1,
                offset=0xA,
                size=0xC8,
            )
            + Op.SSTORE(key=0x6, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        balance=7000,
        nonce=0,
        address=Address("0xaaaf5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    pre[callee] = Account(balance=10, nonce=0)
    pre[callee_1] = Account(balance=0, nonce=1)
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "1122334455667788991011121314151617181920212223242526272829303132"
        ),
        address=Address("0xeeef5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=400000,
    )

    post = {
        contract: Account(
            storage={
                5: 0x11120000000000000000000000000000000000000000000000000000000000,  # noqa: E501
                6: 0x11121314151617181920212223242526272829303132000000000000000000,  # noqa: E501
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
