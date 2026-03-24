"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices
RawCallGasValueTransferMemoryAskFiller.json
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
        "tests/static/state_tests/stEIP150singleCodeGasPrices/RawCallGasValueTransferMemoryAskFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_call_gas_value_transfer_memory_ask(
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
    # { [0] (GAS) (CALL 3000000 <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 10 0 8000 0 8000) [[1]] (SUB @0  (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0x2DC6C0,
                    address=0xE497CD0909C3691E0B6D2A42E26F36696FC27BA5,
                    value=0xA,
                    args_offset=0x0,
                    args_size=0x1F40,
                    ret_offset=0x0,
                    ret_size=0x1F40,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x29902ea04a72cbb6f877f6d27471a102e0700f20"),  # noqa: E501
    )
    callee = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0xe497cd0909c3691e0b6d2a42e26f36696fc27ba5"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=500000,
        value=10,
    )

    post = {
        contract: Account(storage={1: 32308}),
        callee: Account(storage={2: 0x70AC4}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
