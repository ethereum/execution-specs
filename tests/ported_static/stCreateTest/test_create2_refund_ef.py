"""
Test combination of gas refund and EF-prefixed CREATE2 failure.

Ported from:
tests/static/state_tests/stCreateTest/CREATE2_RefundEFFiller.yml
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
    ["tests/static/state_tests/stCreateTest/CREATE2_RefundEFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_refund_ef(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test combination of gas refund and EF-prefixed CREATE2 failure."""
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
    #   sstore(0,0)
    # }
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0x00000000000000000000000000000000005ef94d"),  # noqa: E501
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
    #       // call gas refund provider
    #       let r := call(50000, 0x5ef94d, 0, 0, 0, 0, 0)
    #       // return 0xEF
    #       mstore8(0,0xEF)
    #       return(0,1)
    #     }
    #   }
    # }
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x0]
            + Op.PUSH1[0x19]
            + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x11, size=Op.DUP1)
            + Op.DUP2
            + Op.DUP1
            + Op.SSTORE(key=0x0, value=Op.CREATE2)
            + Op.STOP
            + Op.INVALID
            + Op.POP(
                Op.CALL(
                    gas=0xC350,
                    address=0x5EF94D,
                    value=Op.DUP1,
                    args_offset=Op.DUP1,
                    args_size=Op.DUP1,
                    ret_offset=Op.DUP1,
                    ret_size=0x0,
                ),
            )
            + Op.MSTORE8(offset=0x0, value=0xEF)
            + Op.RETURN(offset=0x0, size=0x1)
        ),
        nonce=0,
        address=Address("0x000000000000000000000000000000000c5ea705"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x5AF3107A4000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        callee: Account(storage={0: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
