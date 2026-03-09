"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall/static_CheckOpcodes4Filler.json
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
    ["tests/static/state_tests/stStaticCall/static_CheckOpcodes4Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_gas_limit, tx_value, expected_post",
    [
        (50000, 0, {}),
        (50000, 100, {}),
        (
            335000,
            0,
            {
                Address("0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49"): Account(
                    storage={
                        1: 1,
                        2: 1,
                        3: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        5: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        6: 0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    }
                )
            },
        ),
        (
            335000,
            100,
            {
                Address("0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49"): Account(
                    storage={
                        1: 1,
                        2: 1,
                        3: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        4: 100,
                        5: 0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                        6: 0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    }
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_check_opcodes4(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    tx_value: int,
    expected_post: dict,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # { [[1]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000001> 0 0 0 0) [[2]] (STATICCALL 100000 <contract:0x1000000000000000000000000000000000000002> 0 0 0 0) [[3]] (CALLER) [[4]] (CALLVALUE) [[5]] (ORIGIN) [[6]] (ADDRESS) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.STATICCALL(
                    gas=0x186A0,
                    address=0x8FD6268252F0D331531601B40524719C7F681FE9,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x3, value=Op.CALLER)
            + Op.SSTORE(key=0x4, value=Op.CALLVALUE)
            + Op.SSTORE(key=0x5, value=Op.ORIGIN)
            + Op.SSTORE(key=0x6, value=Op.ADDRESS)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x3350a62ddddd0ff0e39cd82e2d185fe06b5fcf49"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0x8FD6268252F0D331531601B40524719C7F681FE9,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x8fd6268252f0d331531601b40524719c7f681fe9"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x22,
                condition=Op.EQ(
                    0xFAA10B404AB607779993C016CD5DA73AE1F29D7E,
                    Op.ORIGIN,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x28)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x4B,
                condition=Op.EQ(
                    0x3350A62DDDDD0FF0E39CD82E2D185FE06B5FCF49,
                    Op.CALLER,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x51)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x74,
                condition=Op.EQ(
                    0xB4B91C40F3E3A6E5576B0413572B88D535CEE7B0,
                    Op.ADDRESS,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x7A)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.JUMPI(pc=0x8A, condition=Op.EQ(0x0, Op.CALLVALUE))
            + Op.SSTORE(key=0x1, value=0x2)
            + Op.JUMP(pc=0x90)
            + Op.JUMPDEST
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb4b91c40f3e3a6e5576b0413572b88d535cee7b0"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=tx_value,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
