"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stStaticCall
static_callcallcodecallcode_011_OOGMAfterFiller.json
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
        "tests/static/state_tests/stStaticCall/static_callcallcodecallcode_011_OOGMAfterFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex",
    [
        "000000000000000000000000476564431e8a9c2c934ef7712a1182eebb46b872",
        "000000000000000000000000d678d9a03433a246d441a9a225553d3e4e760c5f",
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_static_callcallcodecallcode_011_oogm_after(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    pre.deploy_contract(
        code=Op.MSTORE(offset=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x335c5531b84765a7626e6e76688f18b81be5259c"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x9C90,
                    address=0xFECF0806036B619896DA47F661DFCE85C0107E9D,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x3, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x476564431e8a9c2c934ef7712a1182eebb46b872"),  # noqa: E501
    )
    # Source: LLL
    # {  [[ 0 ]] (STATICCALL 60140 (CALLDATALOAD 0) 0 64 0 64 ) [[ 1 ]] 1 }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.STATICCALL(
                    gas=0xEAEC,
                    address=Op.CALLDATALOAD(offset=0x0),
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.SSTORE(key=0x1, value=0x1)
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0xb4d115b5309a03febd836abb6456bce43cec037b"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x9C90,
                    address=0xFECF0806036B619896DA47F661DFCE85C0107E9D,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.JUMPDEST
            + Op.JUMPI(
                pc=0x43,
                condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350)),
            )
            + Op.POP(Op.EXTCODESIZE(address=0x1))
            + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
            + Op.JUMP(pc=0x27)
            + Op.JUMPDEST
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xd678d9a03433a246d441a9a225553d3e4e760c5f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x1, value=0x1)
            + Op.POP(
                Op.DELEGATECALL(
                    gas=0x4E34,
                    address=0x335C5531B84765A7626E6E76688F18B81BE5259C,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.MSTORE(offset=0x1, value=0x1)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xfecf0806036b619896da47f661dfce85c0107e9d"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=172000,
    )

    post = {
        contract: Account(storage={1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
