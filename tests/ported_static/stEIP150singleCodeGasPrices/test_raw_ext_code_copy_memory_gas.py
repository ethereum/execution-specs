"""
Test_raw_ext_code_copy_memory_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json
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
    [
        "state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_ext_code_copy_memory_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_raw_ext_code_copy_memory_gas."""
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

    # Source: raw
    # 0x0112233445566778899101112131415161718191202122232425
    addr = pre.deploy_contract(  # noqa: F841
        code=bytes.fromhex(
            "0112233445566778899101112131415161718191202122232425"
        ),
        nonce=0,
        address=Address(0x4A84C43FBA78AE75CBC15C5B63CAA15DA55F4464),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [0] (GAS) (EXTCODECOPY <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 32 0 11120) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.EXTCODECOPY(
            address=0x4A84C43FBA78AE75CBC15C5B63CAA15DA55F4464,
            dest_offset=0x20,
            offset=0x0,
            size=0x2B70,
        )
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address(0x792ED227B10FCD174ACC9E5A69C1F1471A138C5D),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {target: Account(storage={1: 4948})}

    state_test(env=env, pre=pre, post=post, tx=tx)
