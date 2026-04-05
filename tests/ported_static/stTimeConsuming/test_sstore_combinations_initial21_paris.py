"""
Sstore 2 -> {calltype} -> change to {0, 1, 2} |-> {calltype} -> {non,...

Ported from:
state_tests/stTimeConsuming/sstore_combinations_initial21_ParisFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stTimeConsuming/sstore_combinations_initial21_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d",
    range(426),
    ids=lambda d: f"d{d}",
)
@pytest.mark.pre_alloc_mutable
def test_sstore_combinations_initial21_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
) -> None:
    """Sstore 2 -> {calltype} -> change to {0, 1, 2} |-> {calltype} ->..."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB000000000000000000000000000000000000000)
    contract_1 = Address(0xB100000000000000000000000000000000000000)
    contract_2 = Address(0xB200000000000000000000000000000000000000)
    contract_3 = Address(0x1000000000000000000000000000000000000000)
    contract_4 = Address(0x2000000000000000000000000000000000000000)
    contract_5 = Address(0x3000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        nonce=0,
        address=Address(0xB000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={0: 1, 1: 1, 2: 1},
        nonce=0,
        address=Address(0xB100000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { [[0]] 0  [[1]] 1  [[2]] 2 }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x2, value=0x2)
        + Op.STOP,
        storage={0: 2, 1: 2, 2: 2},
        nonce=0,
        address=Address(0xB200000000000000000000000000000000000000),  # noqa: E501
    )
    pre[contract_3] = Account(balance=10, storage={0: 1, 1: 1, 2: 1})
    # Source: lll
    # { [[1]] 1 [[1]] 0 [[2]] 1 [[2]] 0 [[3]] 1 [[3]] 0 [[4]] 1 [[4]] 0 [[5]] 1 [[5]] 0 [[6]] 1 [[6]] 0 [[7]] 1 [[7]] 0 [[8]] 1 [[8]] 0 [[9]] 1 [[9]] 0 [[10]] 1 [[10]] 0 [[11]] 1 [[11]] 0 [[12]] 1 [[12]] 0 [[13]] 1 [[13]] 0 [[14]] 1 [[14]] 0 [[15]] 1 [[15]] 0 [[16]] 1 [[16]] 0  [[1]] 1 }  # noqa: E501
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1)
        + Op.SSTORE(key=0x1, value=0x0)
        + Op.SSTORE(key=0x2, value=0x1)
        + Op.SSTORE(key=0x2, value=0x0)
        + Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x3, value=0x0)
        + Op.SSTORE(key=0x4, value=0x1)
        + Op.SSTORE(key=0x4, value=0x0)
        + Op.SSTORE(key=0x5, value=0x1)
        + Op.SSTORE(key=0x5, value=0x0)
        + Op.SSTORE(key=0x6, value=0x1)
        + Op.SSTORE(key=0x6, value=0x0)
        + Op.SSTORE(key=0x7, value=0x1)
        + Op.SSTORE(key=0x7, value=0x0)
        + Op.SSTORE(key=0x8, value=0x1)
        + Op.SSTORE(key=0x8, value=0x0)
        + Op.SSTORE(key=0x9, value=0x1)
        + Op.SSTORE(key=0x9, value=0x0)
        + Op.SSTORE(key=0xA, value=0x1)
        + Op.SSTORE(key=0xA, value=0x0)
        + Op.SSTORE(key=0xB, value=0x1)
        + Op.SSTORE(key=0xB, value=0x0)
        + Op.SSTORE(key=0xC, value=0x1)
        + Op.SSTORE(key=0xC, value=0x0)
        + Op.SSTORE(key=0xD, value=0x1)
        + Op.SSTORE(key=0xD, value=0x0)
        + Op.SSTORE(key=0xE, value=0x1)
        + Op.SSTORE(key=0xE, value=0x0)
        + Op.SSTORE(key=0xF, value=0x1)
        + Op.SSTORE(key=0xF, value=0x0)
        + Op.SSTORE(key=0x10, value=0x1)
        + Op.SSTORE(key=0x10, value=0x0)
        + Op.SSTORE(key=0x1, value=0x1)
        + Op.STOP,
        nonce=0,
        address=Address(0x2000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # { (REVERT 0 32) }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.REVERT(offset=0x0, size=0x20) + Op.STOP,
        storage={0: 2, 1: 2, 2: 2},
        nonce=0,
        address=Address(0x3000000000000000000000000000000000000000),  # noqa: E501
    )

    tx_data = [
        Op.MSTORE(offset=0x64, value=0x352)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x353)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x354)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x355)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x356)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x357)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x358)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x359)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x35F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x360)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x361)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x362)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x363)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x364)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x365)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x366)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x367)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x368)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x369)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x36F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x370)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x371)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x372)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x373)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x374)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x375)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x376)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x377)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x378)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x379)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x37F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x380)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x381)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x382)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x383)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x384)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x385)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x386)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x387)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x388)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x389)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x38F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x390)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x391)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x392)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x393)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x394)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x395)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x396)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x397)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x398)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x399)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x39F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3A9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AD)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3AF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3B9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BD)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3BF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3C9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CD)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3CF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3D9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DD)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3DF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3E9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3EA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3EB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3EC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3ED)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3EE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3EF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F0)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F1)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F2)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F3)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F4)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F5)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F6)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F7)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F8)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3F9)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FA)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FB)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FC)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FD)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FE)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x3FF)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x400)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x401)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x402)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x403)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x404)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x405)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x406)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x407)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x408)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x409)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x40F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x410)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x411)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x412)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x413)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x414)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x415)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x416)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x417)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x418)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x419)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x41F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x420)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x421)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x422)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x423)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x424)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x425)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x426)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x427)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x428)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x429)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x42F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x430)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x431)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x432)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x433)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x434)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x435)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x436)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x437)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x438)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x439)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x43F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x440)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x441)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x442)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x443)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x444)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x445)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x446)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x447)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x448)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x449)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x44F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x450)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x451)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x452)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x453)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x454)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x455)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x456)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x457)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x458)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x459)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x45F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x460)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x461)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x462)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x463)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x464)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x465)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x466)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x467)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x468)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x469)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x46F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x470)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x471)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x472)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x473)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x474)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x475)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x476)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x477)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x478)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x479)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47A)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47B)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47C)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47D)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47E)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x47F)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x480)
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x481)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x482)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x483)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x484)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x485)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x486)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x487)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x488)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x489)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x48F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x490)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x491)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x492)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x493)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x494)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x495)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x496)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x497)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x498)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x499)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49A)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49B)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49C)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49D)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49E)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x49F)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4A9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4AF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4B9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4BF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4C9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4CF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4D9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DD)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4DF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4E9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4EA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4EB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4EC)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4ED)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4EE)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4EF)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F0)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F1)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F2)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F3)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F4)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F5)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F6)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F7)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_4,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F8)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.STATICCALL(
                gas=0x493E0,
                address=contract_5,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4F9)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_3,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4FA)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_4,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x4FB)
        + Op.POP(
            Op.DELEGATECALL(
                gas=0x493E0,
                address=contract_2,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
                address=contract_2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.POP(
            Op.CALL(
                gas=0x493E0,
                address=contract_5,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
    ]

    # Combinatorial initcode generator
    # 1728 entries = 3 x 12 x 4 x 12 (dims: outer to inner)
    #   dim0: 1st change call type (3) - CALL, CALLCODE, DELEGATECALL
    #   dim1: middle action 1 (12) - {CALL,CALLCODE,DELEGATECALL,STATICCALL} x {c3,c4,c5}
    #   dim2: 2nd change call type (4) - STATICCALL, CALL, CALLCODE, DELEGATECALL
    #   dim3: middle action 2 (12) - {CALL,CALLCODE,DELEGATECALL,STATICCALL} x {c3,c4,c5}
    gas = 0x493E0
    dim0_types = [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
    dim2_types = [Op.STATICCALL, Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
    call_types = [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
    contracts = [contract_3, contract_4, contract_5]
    change_contract = contract_2

    idx = 0x352 + d - 1  # 4-call index

    call_1_op = dim0_types[idx // 576]
    call_2_op = call_types[(idx // 48) % 12 // 3]
    call_2_contract = contracts[(idx // 48) % 12 % 3]
    call_3_op = dim2_types[(idx // 12) % 4]
    call_4_op = call_types[idx % 12 // 3]
    call_4_contract = contracts[idx % 12 % 3]

    initcode = (
        Op.MSTORE(offset=0x64, value=0x352 + d)
        + Op.POP(call_1_op(gas=gas, address=change_contract, args_size=0x20))
        + Op.POP(call_2_op(gas=gas, address=call_2_contract))
        + Op.POP(call_3_op(gas=gas, address=change_contract, args_size=0x20))
        + Op.POP(call_4_op(gas=gas, address=call_4_contract))
        + Op.CALL(gas=gas * 2, address=contract_4)
        + Op.STOP
    )

    assert initcode == tx_data[d]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=2_000_000,
        value=1,
    )

    post = {
        contract_4: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
