"""
test_callcode_sha256_0

Ported from:
state_tests/stPreCompiledContracts2/CALLCODESha256_0Filler.json
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
    ["state_tests/stPreCompiledContracts2/CALLCODESha256_0Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_sha256_0(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcode_sha256_0"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: hex
    # 0x600160005260206000602060006000600260fff2600051600055
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x1)
        + Op.CALLCODE(gas=0xff, address=0x2, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x0, ret_size=0x20)
        + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0)),
        balance=0x1312d00,
        nonce=0,
        address=Address("0xfac135cdecd64b72cda12c2b4764e9d4e474de3e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=365224,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 0xec4916dd28fc4c10d78e287ca5d9cc51ee1ae73cbfde08c6b37324cbfaac8bc5,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
