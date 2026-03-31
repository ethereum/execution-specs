"""
Test if calldata is empty in initcode context.


Ported from:
state_tests/stCreateTest/CREATE2_CallDataFiller.yml
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
    Fork,
)
from execution_testing.vm import Op

from execution_testing.forks import Amsterdam

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CREATE2_CallDataFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_call_data(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """Test if calldata is empty in initcode context."""
    contract_0 = Address(0x000000000000000000000000000000000C5EA705)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000 if fork >= Amsterdam else 1000000,
    )

    pre[sender] = Account(balance=0x5AF3107A4000)
    # Source: yul
    # berlin object "C" {
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
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.PUSH1[0x10]
        + Op.CODECOPY(dest_offset=Op.DUP4, offset=0x11, size=Op.DUP1)
        + Op.DUP2
        + Op.DUP1
        + Op.SSTORE(key=0x0, value=Op.CREATE2)
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=Op.CALLDATALOAD(offset=0x0))
        + Op.CALLDATACOPY(dest_offset=Op.DUP1, offset=0x0, size=0x40)
        + Op.RETURN(offset=0x0, size=Op.MSIZE),
        nonce=0,
        address=Address(0x000000000000000000000000000000000C5EA705),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
    )

    post = {
        contract_0: Account(
            storage={0: 0x7F8330AD7BC2AFE0DFFB2FDC76BBAD8BC326296A},
        ),
        Address(0x7F8330AD7BC2AFE0DFFB2FDC76BBAD8BC326296A): Account(
            code=bytes.fromhex(
                "00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"  # noqa: E501
            ),
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
