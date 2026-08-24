"""
Test_zero_value_call_to_one_storage_key_paris.

Ported from:
state_tests/stZeroCallsTest/ZeroValue_CALL_ToOneStorageKey_ParisFiller.json

@manually-enhanced: Do not overwrite. The contract stores `Op.GAS` into
slot 0, asserting `0x8D5B6` remaining at a fixed execution point, so the
tx gas budget must track the intrinsic across forks. `gas_limit` is
derived as `600_000 + (intrinsic - 21_000)`, where `intrinsic` comes from
`fork.transaction_intrinsic_cost_calculator()`; subtracting the
pre-EIP-2780 baseline intrinsic 21_000 keeps the post-intrinsic execution
budget fixed when EIP-2780 lowers the intrinsic for non-value, non-self
txs. Do not hardcode the literal gas limit.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stZeroCallsTest/ZeroValue_CALL_ToOneStorageKey_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.valid_before("EIP8368")
def test_zero_value_call_to_one_storage_key_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_zero_value_call_to_one_storage_key_paris."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    addr = Address(0x4757608F18B70777AE788DD4056EEED52F7AA68F)
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
    pre[addr] = Account(balance=10, storage={0: 1})
    # Source: lll
    # { [[0]](GAS) [[1]] (CALL 60000 <eoa:0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b> 0 0 0 0 0) [[100]] 1 }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.SSTORE(
            key=0x1,
            value=Op.CALL(
                gas=0xEA60,
                address=0x4757608F18B70777AE788DD4056EEED52F7AA68F,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0xF202BAE278AC09857F5A56991C7A4679632F5841),  # noqa: E501
    )

    # Preserve Cancun's post-intrinsic execution budget across
    # forks; EIP-2780 lowers the intrinsic for non-self non-value
    # txs, and the Op.GAS storage assertion depends on the
    # remaining gas at a fixed execution point.
    intrinsic = fork.transaction_intrinsic_cost_calculator()()
    gas_limit = 600_000 + (intrinsic - 21_000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=gas_limit,
    )

    post = {
        addr: Account(storage={0: 1}, balance=10),
        target: Account(storage={0: 0x8D5B6, 1: 1, 100: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
