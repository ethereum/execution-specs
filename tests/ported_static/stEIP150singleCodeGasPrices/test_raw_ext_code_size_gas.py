"""
Test_raw_ext_code_size_gas.

Ported from:
state_tests/stEIP150singleCodeGasPrices/RawExtCodeSizeGasFiller.json

@manually-enhanced: Do not overwrite. This measures the regular gas
that a single cold `EXTCODESIZE` consumes via `Op.GAS`. EIP-8038
reprices the cold account access (`COLD_ACCOUNT_ACCESS`, 2600 -> 3000)
and charges an extra `WARM_ACCESS` for the opcode's second read (the
code). The stored cost therefore shifts by
`(COLD_ACCOUNT_ACCESS - 2600) + WARM_ACCESS`. The cold term comes from
the fork's own constant; the extra warm term is gated on the
`is_eip_enabled(8037)` flag (the registered flag that activates the
repricing at Amsterdam), so the delta is exactly 0 on earlier forks.
Do not hardcode it.
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
from execution_testing.forks import Fork
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
    gas_costs = fork.gas_costs()
    # EIP-8038: cold account repricing plus the extra warm access charged
    # for the opcode's second read (the code). Both terms are 0 before
    # EIP-8038, so the stored cost is unchanged on earlier forks.
    cold_account_delta = gas_costs.COLD_ACCOUNT_ACCESS - 2600
    code_read_delta = cold_account_delta + (
        gas_costs.WARM_ACCESS if fork.is_eip_enabled(8037) else 0
    )
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
