"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stSystemOperationsTest
callcodeToNameRegistrator0Filler.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stSystemOperationsTest/callcodeToNameRegistrator0Filler.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_to_name_registrator0(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    callee = pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=23,
        nonce=0,
        address=Address("0x15eb18969e0925c8e4a76fd7cbce36a2b056b27e"),  # noqa: E501
    )
    # Source: LLL
    # { (MSTORE 0 0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff) (MSTORE 32 0xaaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa ) [[ 0 ]] (CALLCODE 1000 <contract:0x945304eb96065b2a98b57a48a06ae28d285a71b5> 23 0 64 64 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0xAAFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFAA,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALLCODE(
                    gas=0x3E8,
                    address=0x15EB18969E0925C8E4A76FD7CBCE36A2B056B27E,
                    value=0x17,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x40,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xc390a3ed1719280f32a2a74cbb1f8a3e7b1f002e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex("6000355415600957005b60203560003555")
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "7fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff6000527faaffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffaa602052600060406040600060177315eb18969e0925c8e4a76fd7cbce36a2b056b27e6103e8f260005500"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
