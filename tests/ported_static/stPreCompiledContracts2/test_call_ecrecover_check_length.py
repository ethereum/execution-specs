"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stPreCompiledContracts2
CallEcrecoverCheckLengthFiller.json
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
        "tests/static/state_tests/stPreCompiledContracts2/CallEcrecoverCheckLengthFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_call_ecrecover_check_length(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # { (MSTORE 128 0x1122334455667788990011223344556677889900112233445566778899001122) (MSTORE 0 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c) (MSTORE 32 28) (MSTORE 64 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f) (MSTORE 96 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549) [[ 2 ]] (CALL 300000 1 0 0 128 128 32) [[ 0 ]] (MLOAD 128) [[ 1 ]] (MSIZE) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x80,
                value=0x1122334455667788990011223344556677889900112233445566778899001122,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x0,
                value=0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
            )
            + Op.MSTORE(offset=0x20, value=0x1C)
            + Op.MSTORE(
                offset=0x40,
                value=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x60,
                value=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
            )
            + Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x493E0,
                    address=0x1,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x80,
                    ret_offset=0x80,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x80))
            + Op.SSTORE(key=0x1, value=Op.MSIZE)
            + Op.STOP
        ),
        balance=0x1312D00,
        nonce=0,
        address=Address("0x095e7baea6a6c7c4c2dfeb977efac326af552d87"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=3652240,
        value=100000,
    )

    post = {
        contract: Account(
            storage={
                0: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                1: 160,
                2: 1,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
