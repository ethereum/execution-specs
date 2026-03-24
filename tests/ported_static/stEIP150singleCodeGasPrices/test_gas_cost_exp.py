"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml
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
        "tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000052",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000052",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000084",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000000ffff0000000000000000000000000000000000000000000000000000000000000084",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000b6",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae0000000000000000000000000000000000000000000000000000000000ffffff00000000000000000000000000000000000000000000000000000000000000b6",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000e8",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000ffffffff00000000000000000000000000000000000000000000000000000000000000e8",  # noqa: E501
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_exp(
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'powerOf           0x000)  ; A to the power of @powerOf
    #   (def 'expectedCost      0x020)  ; Expected gas cost
    #   (def 'gasB4             0x040)  ; Before the action being measured
    #   (def 'gasAfter          0x060)  ; After the action being measured
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   [powerOf]       $4
    #   [expectedCost]  $36
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #   [gasB4]    (gas)
    #   (exp 2 @powerOf)
    #   [gasAfter] (gas)
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Return value
    #
    #   [[0]] (- @gasB4 @gasAfter @expectedCost)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x40, value=Op.GAS)
            + Op.POP(Op.EXP(0x2, Op.MLOAD(offset=0x0)))
            + Op.MSTORE(offset=0x60, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x40), Op.MLOAD(offset=0x60)),
                    Op.MLOAD(offset=0x20),
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x087aab8070088fbbe4f60141cf79032d28528b89"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150singleCodeGasPrices/gasCostExpFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000020",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000052",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000000ff0000000000000000000000000000000000000000000000000000000000000052",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000084",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000000ffff0000000000000000000000000000000000000000000000000000000000000084",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000001000000000000000000000000000000000000000000000000000000000000000000b6",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae0000000000000000000000000000000000000000000000000000000000ffffff00000000000000000000000000000000000000000000000000000000000000b6",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae000000000000000000000000000000000000000000000000000000000100000000000000000000000000000000000000000000000000000000000000000000e8",  # noqa: E501
            {},
        ),
        (
            "c5b5a1ae00000000000000000000000000000000000000000000000000000000ffffffff00000000000000000000000000000000000000000000000000000000000000e8",  # noqa: E501
            {},
        ),
    ],
    ids=[
        "case0",
        "case1",
        "case2",
        "case3",
        "case4",
        "case5",
        "case6",
        "case7",
        "case8",
    ],
)
@pytest.mark.pre_alloc_mutable
def test_gas_cost_exp_from_prague(
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
        gas_limit=100000000,
    )

    # Source: LLL
    # {
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Initialization
    #
    #   ; Variables (0x20 byte wide)
    #   (def 'powerOf           0x000)  ; A to the power of @powerOf
    #   (def 'expectedCost      0x020)  ; Expected gas cost
    #   (def 'gasB4             0x040)  ; Before the action being measured
    #   (def 'gasAfter          0x060)  ; After the action being measured
    #
    #   ; Understand CALLDATA. It is four bytes of function
    #   ; selector (irrelevant) followed by 32 byte words
    #   ; of the parameters
    #   [powerOf]       $4
    #   [expectedCost]  $36
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Run the operation
    #   [gasB4]    (gas)
    #   (exp 2 @powerOf)
    #   [gasAfter] (gas)
    #
    #
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Return value
    #
    #   [[0]] (- @gasB4 @gasAfter @expectedCost)
    # }
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.CALLDATALOAD(offset=0x4))
            + Op.MSTORE(offset=0x20, value=Op.CALLDATALOAD(offset=0x24))
            + Op.MSTORE(offset=0x40, value=Op.GAS)
            + Op.POP(Op.EXP(0x2, Op.MLOAD(offset=0x0)))
            + Op.MSTORE(offset=0x60, value=Op.GAS)
            + Op.SSTORE(
                key=0x0,
                value=Op.SUB(
                    Op.SUB(Op.MLOAD(offset=0x40), Op.MLOAD(offset=0x60)),
                    Op.MLOAD(offset=0x20),
                ),
            )
            + Op.STOP
        ),
        storage={0x0: 0x60A7},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address("0x087aab8070088fbbe4f60141cf79032d28528b89"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=16777216,
        value=1,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
