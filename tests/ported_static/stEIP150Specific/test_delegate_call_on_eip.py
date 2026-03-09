"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json
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
    ["tests/static/state_tests/stEIP150Specific/DelegateCallOnEIPFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_delegate_call_on_eip(
    state_test: StateTestFiller,
    pre: Alloc,
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
    # { [8] (GAS) (SSTORE 9 (DELEGATECALL 600000 <contract:0x1000000000000000000000000000000000000105> 0 0 0 0)) [[8]] (SUB @8 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x8, value=Op.GAS)
            + Op.SSTORE(
                key=0x9,
                value=Op.DELEGATECALL(
                    gas=0x927C0,
                    address=0xFD59ABAE521384B5731AC657616680219FBC423D,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x8, value=Op.SUB(Op.MLOAD(offset=0x8), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x90bc108216940a7ddaf3ba6624f2fdbe4c5e83dc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x12) + Op.STOP,
        nonce=0,
        address=Address("0xfd59abae521384b5731ac657616680219fbc423d"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(storage={0: 18, 8: 46841, 9: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
