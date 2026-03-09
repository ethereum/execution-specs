"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stReturnDataTest
create_callprecompile_returndatasizeFiller.json
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
        "tests/static/state_tests/stReturnDataTest/create_callprecompile_returndatasizeFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_callprecompile_returndatasize(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x834185262E53584684BF2B72C64E510013C235D0F45E462DB65900455DF45A35
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=111669149696,
    )

    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x111122223333444455556666777788889999AAAABBBBCCCCDDDDEEEEFFFF,  # noqa: E501
            )
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x9898dd5e5c526b55ec49b1047e298705c13279f1"),  # noqa: E501
    )
    # Source: LLL
    # { (seq (CREATE 0 0 (lll (seq (mstore 0 0x112233) (CALL 0x9000 4 0 0 32 0 32) (SSTORE 0 (RETURNDATASIZE)) (RETURN 0 32) (STOP) ) 0)) (SSTORE 0 (RETURNDATASIZE)) (STOP) )}  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.PUSH1[0x23]
            + Op.CODECOPY(dest_offset=0x0, offset=0x15, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.POP(Op.CREATE)
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.STOP
            + Op.STOP
            + Op.INVALID
            + Op.MSTORE(offset=0x0, value=0x112233)
            + Op.POP(
                Op.CALL(
                    gas=0x9000,
                    address=0x4,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x20,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.RETURNDATASIZE)
            + Op.RETURN(offset=0x0, size=0x20)
            + Op.STOP
            + Op.STOP
        ),
        storage={0x0: 0x1},
        nonce=0,
        address=Address("0xa2412b1e2a1e23e8fd87f52566c8a89f48682676"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x6400000000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=100000,
    )

    post = {
        Address("0xf234137fe508cc371f3da359ab482e4138d0b0c9"): Account(
            storage={0: 32},
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
