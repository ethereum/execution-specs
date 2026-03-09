"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls
NewGasPriceForCodesWithMemExpandingCallsFiller.json
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
        "tests/static/state_tests/stMemExpandingEIP150Calls/NewGasPriceForCodesWithMemExpandingCallsFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_new_gas_price_for_codes_with_mem_expanding_calls(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x03956FC06BD55836ACDB92DA0E38A15F2E568C088022CF2278180477F3F7702A
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.EXTCODESIZE(
                    address=0x6B6AF3C6E1714081C8C3085ACBAC8C2B21FADF0B,
                ),
            )
            + Op.EXTCODECOPY(
                address=0x6B6AF3C6E1714081C8C3085ACBAC8C2B21FADF0B,
                dest_offset=0x0,
                offset=0x0,
                size=0x14,
            )
            + Op.SSTORE(key=0x2, value=Op.MLOAD(offset=0x0))
            + Op.SSTORE(key=0x4, value=Op.SLOAD(key=0x0))
            + Op.SSTORE(
                key=0x5,
                value=Op.CALL(
                    gas=0x7530,
                    address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                    value=0x1,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
            + Op.SSTORE(
                key=0x6,
                value=Op.CALLCODE(
                    gas=0x7530,
                    address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                    value=0x1,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
            + Op.SSTORE(
                key=0x7,
                value=Op.DELEGATECALL(
                    gas=0x7530,
                    address=0x7B8C83E74CC8DFADB03138C2743C70588ACE4222,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
            + Op.SSTORE(
                key=0x8,
                value=Op.CALL(
                    gas=0x7530,
                    address=0x1000000000000000000000000000000000000013,
                    value=0x0,
                    args_offset=0xFF,
                    args_size=0xFF,
                    ret_offset=0xFF,
                    ret_size=0xFF,
                ),
            )
            + Op.SSTORE(
                key=0x3,
                value=Op.BALANCE(
                    address=0xF1100237A29F570CBF8B107BA3CB5BF2DB42BD3F,
                ),
            )
            + Op.SSTORE(key=0xA, value=Op.GAS)
        ),
        storage={0x0: 0x12},
        nonce=0,
        address=Address("0x23a2ec54f5f8589778da7c2199caf3b179a24cb9"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=bytes.fromhex(
            "1122334455667788991011121314151617181920212223242526272829303132"
        ),
        balance=111,
        nonce=0,
        address=Address("0x6b6af3c6e1714081c8c3085acbac8c2b21fadf0b"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=Op.SSTORE(key=0x64, value=0x11),
        nonce=0,
        address=Address("0x7b8c83e74cc8dfadb03138c2743c70588ace4222"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A5100000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(
            storage={
                0: 18,
                1: 32,
                2: 0x1122334455667788991011121314151617181920000000000000000000000000,  # noqa: E501
                3: 0xE8D4A4B47280,
                4: 18,
                7: 1,
                8: 1,
                10: 0x60AE9,
                100: 17,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
