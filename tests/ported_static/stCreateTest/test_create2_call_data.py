"""
Test if calldata is empty in initcode context.

Ported from:
tests/static/state_tests/stCreateTest/CREATE2_CallDataFiller.yml
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
    ["tests/static/state_tests/stCreateTest/CREATE2_CallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_call_data(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test if calldata is empty in initcode context."""
    coinbase = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    # Source: Yul
    # {
    #   code {
    #     let s := datasize("initcode")
    #     let o := dataoffset("initcode")
    #     codecopy(0, o, s)
    #     let r := create2(0, 0, s, 0)
    #     sstore(0, r)
    #     stop()
    #   }
    #
    #   object "initcode" {
    #     code {
    #       sstore(0, calldataload(0))
    #       calldatacopy(0, 0, 64)
    #       return(0, msize())
    #     }
    #   }
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x10]
            + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x11, size=Op.DUP1)
            + Op.DUP2
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE2)
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0))
            + Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x40)
            + Op.RETURN(offset=0x0, size=Op.MSIZE)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000c5ea705"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5AF3107A4000)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract: Account(
                    storage={0: 0x7F8330AD7BC2AFE0DFFB2FDC76BBAD8BC326296A},
                    code=bytes.fromhex(
                        "6000601080601183398180f560005500fe600035600055604060008037596000f3"  # noqa: E501
                    ),
                ),
                Address("0x7f8330ad7bc2afe0dffb2fdc76bbad8bc326296a"): Account(
                    code=bytes.fromhex(
                        "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
