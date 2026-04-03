"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml
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
    ["state_tests/stEIP150singleCodeGasPrices/gasCostReturnFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_gas_cost_return(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: raw
    # 0x600060FF00
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0] + Op.PUSH1[0xFF] + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xEB0E68B88A12FC84AD4A1EEB07B289638C4D9F3C),  # noqa: E501
    )
    # Source: raw
    # 0x600060FFF3
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0xFF, size=0x0),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x35CD99E56B0F9AC243172A86BEF4D042DFDBC166),  # noqa: E501
    )
    # Source: lll
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'gasB4         0x000)  ; Before the action being measured
    #
    #   ; Gas for the STOP call
    #   (def 'gasSTOP       0x020)
    #
    #   ; Gas for the RETURN call
    #   (def 'gasRETURN     0x040)
    #
    #   ; Play with the variables here to avoid having the memory allocation
    #   ; affect the gas calculation
    #   [gasB4] 0x60A7
    #   [gasSTOP] 0x60A7
    #   [gasRETURN] 0x60A7
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #
    #   [gasB4] (gas)
    #   (call 0x10000 0x1000 0 0 0 0 0)
    #   [gasSTOP] (- @gasB4 (gas))
    #
    #
    #   [gasB4] (gas)
    #   (call 0x10000 0x2000 0 0 0 0 0)
    #   [gasRETURN] (- @gasB4 (gas))
    # ... (11 more lines)
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x60A7)
        + Op.MSTORE(offset=0x20, value=0x60A7)
        + Op.MSTORE(offset=0x40, value=0x60A7)
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0x1000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x20, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(
            Op.CALL(
                gas=0x10000,
                address=0x2000,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x40, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.SSTORE(
            key=0x0, value=Op.SUB(Op.MLOAD(offset=0x20), Op.MLOAD(offset=0x40))
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x155665FB22995BB5B9DC1D8D9D57A00AC64DC1E0),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("00"),
        gas_limit=16777216,
        value=1,
    )

    post = {target: Account(storage={0: 0, 1: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
