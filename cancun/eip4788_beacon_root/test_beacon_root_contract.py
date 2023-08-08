"""
abstract: Tests beacon block root for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

    Test the exposed beacon chain root in the EVM for [EIP-4788: Beacon block root in the EVM](https://eips.ethereum.org/EIPS/eip-4788)

note: Adding a new test

    Add a function that is named `test_<test_name>` and takes at least the following arguments:

    - state_test
    - env
    - pre
    - tx
    - post
    - valid_call

    The following arguments *need* to be parametrized or the test will not be generated:

    -

    All other `pytest.fixtures` can be parametrized to generate new combinations and test
    cases.

"""  # noqa: E501

from typing import Dict

import pytest

from ethereum_test_tools import Environment, StateTestFiller, Transaction
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .common import BEACON_ROOT_CONTRACT_CALL_GAS, REF_SPEC_4788_GIT_PATH, REF_SPEC_4788_VERSION

REFERENCE_SPEC_GIT_PATH = REF_SPEC_4788_GIT_PATH
REFERENCE_SPEC_VERSION = REF_SPEC_4788_VERSION


@pytest.mark.parametrize(
    "call_gas, valid_call",
    [
        pytest.param(BEACON_ROOT_CONTRACT_CALL_GAS, True),
        pytest.param(BEACON_ROOT_CONTRACT_CALL_GAS + 1, True),
        pytest.param(
            BEACON_ROOT_CONTRACT_CALL_GAS - 1,
            False,
            marks=pytest.mark.xfail(reason="gas calculation is incorrect"),  # TODO
        ),
    ],
)
@pytest.mark.parametrize(
    "call_type,call_value,valid_input",
    [
        (Op.CALL, 1, True),
        (Op.CALL, 0, True),
        (Op.CALLCODE, 0, False),
        (Op.DELEGATECALL, 0, False),
        (Op.STATICCALL, 0, True),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_precompile_calls(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call using various call contexts:
    - `CALL`
    - `DELEGATECALL`
    - `CALLCODE`
    - `STATICCALL`
    for different call gas amounts:
    - exact gas (valid call)
    - extra gas (valid call)
    - insufficient gas (invalid call)

    The expected result is that the precompile call will be executed if the gas amount is met
    and return the correct`parent_beacon_block_root`. Otherwise the call will be invalid, and not
    be executed. This is highlighted within storage by storing the return value of each call
    context.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "timestamp, valid_input",
    [
        (0x0C, True),  # twelve
        (2**32, True),  # arbitrary
        (2**64 - 2, True),  # near-max
        (2**64 - 1, True),  # max
        # TODO: Update t8n to un marshal > 64-bit int
        # Exception: failed to evaluate: ERROR(10): failed un marshaling stdin
        # (2**64, False),  # overflow
        # Exception: failed to evaluate: ERROR(10): failed un marshaling stdin
        # (2**64 + 1, False),  # overflow+1
    ],
)
@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.parametrize(
    "system_address_balance",
    [
        pytest.param(0, id="empty_system_address"),
        pytest.param(1, id="one_wei_system_address"),
        pytest.param(int(1e18), id="one_eth_system_address"),
    ],
)
@pytest.mark.valid_from("Cancun")
def test_beacon_root_precompile_timestamps(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call across for various valid and invalid timestamps.

    The expected result is that the precompile call will return the correct
    `parent_beacon_block_root` for a valid input timestamp and return the zero'd 32 bytes value
    for an invalid input timestamp.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "tx_data",
    [
        pytest.param(bytes(), id="empty_calldata"),
        pytest.param(int.to_bytes(12, length=1, byteorder="big"), id="one_byte"),
        pytest.param(int.to_bytes(12, length=31, byteorder="big"), id="31_bytes"),
        pytest.param(int.to_bytes(12, length=33, byteorder="big"), id="33_bytes"),
        pytest.param(int.to_bytes(12, length=1024, byteorder="big"), id="1024_bytes"),
    ],
)
@pytest.mark.parametrize("valid_call,valid_input", [(False, False)])
@pytest.mark.parametrize("timestamp", [12])
@pytest.mark.valid_from("Cancun")
def test_calldata_lengths(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call using multiple invalid input lengths.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize(
    "beacon_root, timestamp",
    [
        (12, 12),  # twelve
        (2**32, 2**32),  # arbitrary
        (2**64 - 2, 2**64 - 2),  # near-max
        (2**64 - 1, 2**64 - 1),  # max
    ],
    indirect=["beacon_root"],
)
@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.valid_from("Cancun")
def test_beacon_root_equal_to_timestamp(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call where the beacon root is equal to the timestamp.

    The expected result is that the precompile call will return the `parent_beacon_block_root`,
    as all timestamps used are valid.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )


@pytest.mark.parametrize("tx_type", range(4))
@pytest.mark.parametrize("auto_access_list", [False, True])
@pytest.mark.parametrize("call_beacon_root_contract", [True])
@pytest.mark.valid_from("Cancun")
def test_tx_to_beacon_root_contract(
    state_test: StateTestFiller,
    env: Environment,
    pre: Dict,
    tx: Transaction,
    post: Dict,
):
    """
    Tests the beacon root precompile call using a transaction to the precompile contract, using
    different transaction types and data lengths.
    """
    state_test(
        env=env,
        pre=pre,
        txs=[tx],
        post=post,
    )
