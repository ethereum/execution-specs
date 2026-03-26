"""
test_raw_ext_code_copy_memory_gas

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json
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
    ["state_tests/stEIP150singleCodeGasPrices/RawExtCodeCopyMemoryGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_ext_code_copy_memory_gas(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_raw_ext_code_copy_memory_gas"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: raw
    # 0x0112233445566778899101112131415161718191202122232425
    addr_0x094f5374fce5edbc8e2a8697c15331677e6ebf0b = pre.deploy_contract(
        code=bytes.fromhex("0112233445566778899101112131415161718191202122232425"),  # noqa: E501
        nonce=0,
        address=Address("0x4a84c43fba78ae75cbc15c5b63caa15da55f4464"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0] (GAS) (EXTCODECOPY <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b> 32 0 11120) [[1]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.EXTCODECOPY(address=0x4a84c43fba78ae75cbc15c5b63caa15da55f4464, dest_offset=0x20, offset=0x0, size=0x2b70)
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address("0x792ed227b10fcd174acc9e5a69c1f1471a138c5d"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={1: 4948})}

    state_test(env=env, pre=pre, post=post, tx=tx)
