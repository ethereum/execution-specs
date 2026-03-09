"""
Potentially broken test: gas optimization shows that we can go as low as...

Ported from:
tests/static/state_tests/stQuadraticComplexityTest
Call20KbytesContract50_3Filler.json
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
        "tests/static/state_tests/stQuadraticComplexityTest/Call20KbytesContract50_3Filler.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.parametrize(
    "tx_gas_limit, expected_post",
    [
        (150000, {}),
        (
            250000000,
            {
                Address("0x2c496c63f4e9f426bfd41214147cdd3dcd2de1c3"): Account(
                    storage={0: 2}
                ),
                Address("0x8c9ec19d542269495230087c08602e5d70572fd5"): Account(
                    storage={0: 1, 1: 50}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_call20_kbytes_contract50_3(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_gas_limit: int,
    expected_post: dict,
) -> None:
    """Potentially broken test: gas optimization shows that we can go as..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0xE7C72B378297589ACEE4E0BA3272841BCFC5E220F86DE253F890274CFEE9E474
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=882500000000,
    )

    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.PUSH1[0x1]
        + Op.JUMP(pc=0x4A8E)
        + Op.JUMPDEST * 21125
        + Op.PUSH1[0x1]
        + Op.SSTORE(key=0x0, value=Op.ADD),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x2c496c63f4e9f426bfd41214147cdd3dcd2de1c3"),
    )
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
    # Source: LLL
    # { (def 'i 0x80) (for {} (< @i 50) [i](+ @i 1) [[ 0 ]] (CALL 88250000000 <contract:0xaaa50000fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) ) [[ 1 ]] @i }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.JUMPDEST
            + Op.JUMPI(
                pc=0x40,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0x32)),
            )
            + Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=0x148C1C2280,
                    address=0x2C496C63F4E9F426BFD41214147CDD3DCD2DE1C3,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x0)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x80))
            + Op.STOP
        ),
        balance=0xFFFFFFFFFFFFF,
        nonce=0,
        address=Address("0x8c9ec19d542269495230087c08602e5d70572fd5"),
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=tx_gas_limit,
        value=10,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
