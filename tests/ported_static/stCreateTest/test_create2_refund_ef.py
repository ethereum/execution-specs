"""
Test combination of gas refund and EF-prefixed CREATE2 failure.


Ported from:
state_tests/stCreateTest/CREATE2_RefundEFFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE2_RefundEFFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_refund_ef(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test combination of gas refund and EF-prefixed CREATE2 failure."""
    contract_0 = Address(0x00000000000000000000000000000000005EF94D)
    contract_1 = Address(0x000000000000000000000000000000000C5EA705)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: yul
    # london {
    #   sstore(0,0)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.DUP1, value=0x0) + Op.STOP,
        storage={0: 1},
        nonce=0,
        address=Address(0x00000000000000000000000000000000005EF94D),  # noqa: E501
    )
    # Source: yul
    # london object "C" {
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
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
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
                address=contract_0,
                value=Op.DUP1,
                args_offset=Op.DUP1,
                args_size=Op.DUP1,
                ret_offset=Op.DUP1,
                ret_size=0x0,
            )
        )
        + Op.MSTORE8(offset=0x0, value=0xEF)
        + Op.RETURN(offset=0x0, size=0x1),
        nonce=0,
        address=Address(0x000000000000000000000000000000000C5EA705),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=Bytes(""),
        gas_limit=100000,
    )

    post = {
        contract_0: Account(storage={0: 1}),
        Address(
            0xBE8F87148D0767989CCE2E6A6A5D91C7D0C840E0
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
