"""
Test_suicide_to_not_existing_contract.

Ported from:
state_tests/stEIP150Specific/SuicideToNotExistingContractFiller.json
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
    ["state_tests/stEIP150Specific/SuicideToNotExistingContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_to_not_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_suicide_to_not_existing_contract."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000116> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0xEA60,
                address=0x9D6D7885D3D58A49C8352635776C205F722501C,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0xBABAE893BEE69E2141E0E92F2251664AC445EA2A),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT 0x2000000000000000000000000000000000000115) }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SELFDESTRUCT(
            address=0x2000000000000000000000000000000000000115
        )
        + Op.STOP,
        nonce=0,
        address=Address(0x09D6D7885D3D58A49C8352635776C205F722501C),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        addr: Account(
            storage={},
            code=bytes.fromhex(
                "732000000000000000000000000000000000000115ff00"
            ),
            balance=0,
            nonce=0,
        ),
        target: Account(storage={1: 10237}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
