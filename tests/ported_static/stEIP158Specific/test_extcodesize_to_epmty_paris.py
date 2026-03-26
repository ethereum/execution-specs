"""
test_extcodesize_to_epmty_paris

Ported from:
state_tests/stEIP158Specific/EXTCODESIZE_toEpmtyParisFiller.json
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
    ["state_tests/stEIP158Specific/EXTCODESIZE_toEpmtyParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodesize_to_epmty_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_extcodesize_to_epmty_paris"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b = Address("0x76fae819612a29489a1a43208613d8f8557b8898")  # noqa: E501
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0](GAS) [[1]] (EXTCODESIZE <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b>) [[100]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.SSTORE(key=0x1, value=Op.EXTCODESIZE(address=0x76fae819612a29489a1a43208613d8f8557b8898))  # noqa: E501
        + Op.SSTORE(key=0x64, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        storage={1: 1536},
        nonce=0,
        address=Address("0x6a7ca130ba6213231c23332fa5fcab8ccb85c04b"),  # noqa: E501
    )
    pre[addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b] = Account(balance=10)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b: Account(storage={}, code=b"", balance=10, nonce=0),
        target: Account(storage={100: 7617}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
