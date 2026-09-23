"""
Test_raw_ext_code_size_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawExtCodeSizeGasFiller.json

@manually-enhanced: Do not overwrite. This measures the regular gas
that a single cold `EXTCODESIZE` consumes via `Op.GAS`. EIP-8038
raises the cold account access (`COLD_ACCOUNT_ACCESS`) and charges an
extra `WARM_ACCESS` for the opcode's second read (the code). The
stored cost therefore shifts by the opcode's own cold cost on the fork
less its cost on Cancun, taken from `Op.EXTCODESIZE` metadata so the
delta is exactly 0 on earlier forks. Do not hardcode it.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Cancun, Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/RawExtCodeSizeGasFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_raw_ext_code_size_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test_raw_ext_code_size_gas."""
    # EIP-8038 delta, 0 before EIP-8038: the cold account reprice plus a
    # second WARM_ACCESS for the code read, both carried by the opcode's
    # cost metadata.
    cold_extcodesize = Op.EXTCODESIZE.with_metadata(address_warm=False)
    cancun_extcodesize_cost = cold_extcodesize.gas_cost(Cancun)
    code_read_delta = cold_extcodesize.gas_cost(fork) - cancun_extcodesize_cost
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = pre.fund_eoa(amount=0xE8D4A51000)

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
    )
    # Source: lll
    # { [0] (GAS) (EXTCODESIZE <contract:0x094f5374fce5edbc8e2a8697c15331677e6ebf0b>) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.EXTCODESIZE(address=addr))
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {target: Account(storage={1: 2616 + code_read_delta})}

    state_test(env=env, pre=pre, post=post, tx=tx)
