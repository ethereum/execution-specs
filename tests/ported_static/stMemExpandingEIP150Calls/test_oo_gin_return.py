"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stMemExpandingEIP150Calls/OOGinReturnFiller.yml
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
        "tests/static/state_tests/stMemExpandingEIP150Calls/OOGinReturnFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "1a8451e60000000000000000000000009f5c4c430e37b429d18f8aba147e2302af08f2100000000000000000000000000000000000000000000000000000000000000036",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0xDEAD60A7, 1: 0xDEAD60A7}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000cee9f0c6117cc881ad7b4c378c2bebee8fcd04a90000000000000000000000000000000000000000000000000000000000000036",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0xDEAD60A7, 1: 0xDEAD60A7}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000009f5c4c430e37b429d18f8aba147e2302af08f2100000000000000000000000000000000000000000000000000000000000000025",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0x60A760A7}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000cee9f0c6117cc881ad7b4c378c2bebee8fcd04a90000000000000000000000000000000000000000000000000000000000000025",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0x60A760A7}
                )
            },
        ),
        (
            "1a8451e60000000000000000000000009f5c4c430e37b429d18f8aba147e2302af08f2100000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0x60A760A7}
                )
            },
        ),
        (
            "1a8451e6000000000000000000000000cee9f0c6117cc881ad7b4c378c2bebee8fcd04a90000000000000000000000000000000000000000000000000000000000000010",  # noqa: E501
            {
                Address("0xebd3191dd8150f47e30f87927db4592163ee9224"): Account(
                    storage={0: 0x60A760A7}
                )
            },
        ),
    ],
    ids=["case0", "case1", "case2", "case3", "case4", "case5"],
)
@pytest.mark.pre_alloc_mutable
def test_oo_gin_return(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Ori Pomerantz qbzzt1@gmail.com."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x40AC0FC28C27E961EE46EC43355A094DE205856EDBD4654CF2577C2608D4EC1E
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xDEAD60A7)
            + Op.RETURN(offset=0x0, size=0x100)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x9f5c4c430e37b429d18f8aba147e2302af08f210"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0xDEAD60A7)
            + Op.REVERT(offset=0x0, size=0x100)
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xcee9f0c6117cc881ad7b4c378c2bebee8fcd04a9"),  # noqa: E501
    )
    # Source: LLL
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'callRet    0x100)
    #   (def 'type       0x120)
    #   (def 'gas2Use    0x140)
    #   (def 'retVal     0x160)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Understand the input.
    #   [type]       $4
    #   [gas2Use]    $36
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   [0] 0x60A760A7
    #   [callRet] (call @gas2Use
    #                   @type
    #                   0
    #                   0 0
    #                   0 0x100)
    #   [[0]] @0    ; first 0x20 bytes of return data
    #   (if (> (returndatasize) 0) (returndatacopy retVal 0 0x20) NOP)
    #   [[1]] @retVal
    # }   ; end of LLL code
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x120, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x140, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x0, value=0x60A760A7)
            + Op.MSTORE(
                offset=0x100,
                value=Op.CALL(
                    gas=Op.MLOAD(offset=0x140),
                    address=Op.MLOAD(offset=0x120),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x100,
                ),
            )
            + Op.SSTORE(key=0x0, value=Op.MLOAD(offset=0x0))
            + Op.JUMPI(pc=0x41, condition=Op.GT(Op.RETURNDATASIZE, 0x0))
            + Op.POP(0x0)
            + Op.JUMP(pc=0x4A)
            + Op.JUMPDEST
            + Op.RETURNDATACOPY(dest_offset=0x160, offset=0x0, size=0x20)
            + Op.JUMPDEST
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x160))
            + Op.STOP
        ),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0xebd3191dd8150f47e30f87927db4592163ee9224"),  # noqa: E501
    )

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=9437184,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
