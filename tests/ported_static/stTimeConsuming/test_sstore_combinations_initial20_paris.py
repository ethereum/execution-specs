"""
Sstore 2 -> {calltype} -> change to {0, 1, 2} |-> {calltype} -> {non,...

Ported from:
state_tests/stTimeConsuming/sstore_combinations_initial20_ParisFiller.json
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
        "state_tests/stTimeConsuming/sstore_combinations_initial20_ParisFiller.json"  # noqa: E501
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
def test_sstore_combinations_initial20_paris(
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
        Op.MSTORE(offset=0x64, value=0x0)
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
        + Op.CALL(
            gas=0x927C0,
            address=contract_4,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        Op.MSTORE(offset=0x64, value=0x1)
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
        Op.MSTORE(offset=0x64, value=0x2)
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
        Op.MSTORE(offset=0x64, value=0x3)
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
        Op.MSTORE(offset=0x64, value=0x4)
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
        Op.MSTORE(offset=0x64, value=0x5)
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
        Op.MSTORE(offset=0x64, value=0x6)
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
        Op.MSTORE(offset=0x64, value=0x7)
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
        Op.MSTORE(offset=0x64, value=0x8)
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
        Op.MSTORE(offset=0x64, value=0x9)
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
        Op.MSTORE(offset=0x64, value=0xA)
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
        Op.MSTORE(offset=0x64, value=0xB)
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
        Op.MSTORE(offset=0x64, value=0xC)
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
        Op.MSTORE(offset=0x64, value=0xD)
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
        Op.MSTORE(offset=0x64, value=0xE)
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
        Op.MSTORE(offset=0x64, value=0xF)
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
        Op.MSTORE(offset=0x64, value=0x10)
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
        Op.MSTORE(offset=0x64, value=0x11)
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
        Op.MSTORE(offset=0x64, value=0x12)
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
        Op.MSTORE(offset=0x64, value=0x13)
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
        Op.MSTORE(offset=0x64, value=0x14)
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
        Op.MSTORE(offset=0x64, value=0x15)
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
        Op.MSTORE(offset=0x64, value=0x16)
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
        Op.MSTORE(offset=0x64, value=0x17)
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
        Op.MSTORE(offset=0x64, value=0x18)
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
        Op.MSTORE(offset=0x64, value=0x19)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x20)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x21)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x22)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x23)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x24)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x25)
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
        Op.MSTORE(offset=0x64, value=0x26)
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
        Op.MSTORE(offset=0x64, value=0x27)
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
        Op.MSTORE(offset=0x64, value=0x28)
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
        Op.MSTORE(offset=0x64, value=0x29)
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
        Op.MSTORE(offset=0x64, value=0x2A)
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
        Op.MSTORE(offset=0x64, value=0x2B)
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
        Op.MSTORE(offset=0x64, value=0x2C)
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
        Op.MSTORE(offset=0x64, value=0x2D)
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
        Op.MSTORE(offset=0x64, value=0x2E)
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
        Op.MSTORE(offset=0x64, value=0x2F)
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
        Op.MSTORE(offset=0x64, value=0x30)
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
        Op.MSTORE(offset=0x64, value=0x31)
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
        Op.MSTORE(offset=0x64, value=0x32)
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
        Op.MSTORE(offset=0x64, value=0x33)
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
        Op.MSTORE(offset=0x64, value=0x34)
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
        Op.MSTORE(offset=0x64, value=0x35)
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
        Op.MSTORE(offset=0x64, value=0x36)
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
        Op.MSTORE(offset=0x64, value=0x37)
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
        Op.MSTORE(offset=0x64, value=0x38)
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
        Op.MSTORE(offset=0x64, value=0x39)
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
        Op.MSTORE(offset=0x64, value=0x3A)
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
        Op.MSTORE(offset=0x64, value=0x3B)
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
        Op.MSTORE(offset=0x64, value=0x3C)
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
        Op.MSTORE(offset=0x64, value=0x3D)
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
        Op.MSTORE(offset=0x64, value=0x3E)
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
        Op.MSTORE(offset=0x64, value=0x3F)
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
        Op.MSTORE(offset=0x64, value=0x40)
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
        Op.MSTORE(offset=0x64, value=0x41)
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
        Op.MSTORE(offset=0x64, value=0x42)
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
        Op.MSTORE(offset=0x64, value=0x43)
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
        Op.MSTORE(offset=0x64, value=0x44)
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
        Op.MSTORE(offset=0x64, value=0x45)
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
        Op.MSTORE(offset=0x64, value=0x46)
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
        Op.MSTORE(offset=0x64, value=0x47)
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
        Op.MSTORE(offset=0x64, value=0x48)
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
        Op.MSTORE(offset=0x64, value=0x49)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x4F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x50)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x51)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x52)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x53)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x54)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x55)
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
        Op.MSTORE(offset=0x64, value=0x56)
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
        Op.MSTORE(offset=0x64, value=0x57)
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
        Op.MSTORE(offset=0x64, value=0x58)
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
        Op.MSTORE(offset=0x64, value=0x59)
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
        Op.MSTORE(offset=0x64, value=0x5A)
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
        Op.MSTORE(offset=0x64, value=0x5B)
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
        Op.MSTORE(offset=0x64, value=0x5C)
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
        Op.MSTORE(offset=0x64, value=0x5D)
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
        Op.MSTORE(offset=0x64, value=0x5E)
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
        Op.MSTORE(offset=0x64, value=0x5F)
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
        Op.MSTORE(offset=0x64, value=0x60)
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
        Op.MSTORE(offset=0x64, value=0x61)
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
        Op.MSTORE(offset=0x64, value=0x62)
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
        Op.MSTORE(offset=0x64, value=0x63)
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
        Op.MSTORE(offset=0x64, value=0x64)
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
        Op.MSTORE(offset=0x64, value=0x65)
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
        Op.MSTORE(offset=0x64, value=0x66)
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
        Op.MSTORE(offset=0x64, value=0x67)
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
        Op.MSTORE(offset=0x64, value=0x68)
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
        Op.MSTORE(offset=0x64, value=0x69)
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
        Op.MSTORE(offset=0x64, value=0x6A)
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
        Op.MSTORE(offset=0x64, value=0x6B)
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
        Op.MSTORE(offset=0x64, value=0x6C)
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
        Op.MSTORE(offset=0x64, value=0x6D)
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
        Op.MSTORE(offset=0x64, value=0x6E)
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
        Op.MSTORE(offset=0x64, value=0x6F)
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
        Op.MSTORE(offset=0x64, value=0x70)
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
        Op.MSTORE(offset=0x64, value=0x71)
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
        Op.MSTORE(offset=0x64, value=0x72)
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
        Op.MSTORE(offset=0x64, value=0x73)
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
        Op.MSTORE(offset=0x64, value=0x74)
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
        Op.MSTORE(offset=0x64, value=0x75)
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
        Op.MSTORE(offset=0x64, value=0x76)
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
        Op.MSTORE(offset=0x64, value=0x77)
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
        Op.MSTORE(offset=0x64, value=0x78)
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
        Op.MSTORE(offset=0x64, value=0x79)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x7F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x80)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x81)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x82)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x83)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x84)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x85)
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
        Op.MSTORE(offset=0x64, value=0x86)
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
        Op.MSTORE(offset=0x64, value=0x87)
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
        Op.MSTORE(offset=0x64, value=0x88)
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
        Op.MSTORE(offset=0x64, value=0x89)
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
        Op.MSTORE(offset=0x64, value=0x8A)
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
        Op.MSTORE(offset=0x64, value=0x8B)
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
        Op.MSTORE(offset=0x64, value=0x8C)
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
        Op.MSTORE(offset=0x64, value=0x8D)
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
        Op.MSTORE(offset=0x64, value=0x8E)
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
        Op.MSTORE(offset=0x64, value=0x8F)
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
        Op.MSTORE(offset=0x64, value=0x90)
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
        Op.MSTORE(offset=0x64, value=0x91)
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
        Op.MSTORE(offset=0x64, value=0x92)
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
        Op.MSTORE(offset=0x64, value=0x93)
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
        Op.MSTORE(offset=0x64, value=0x94)
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
        Op.MSTORE(offset=0x64, value=0x95)
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
        Op.MSTORE(offset=0x64, value=0x96)
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
        Op.MSTORE(offset=0x64, value=0x97)
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
        Op.MSTORE(offset=0x64, value=0x98)
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
        Op.MSTORE(offset=0x64, value=0x99)
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
        Op.MSTORE(offset=0x64, value=0x9A)
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
        Op.MSTORE(offset=0x64, value=0x9B)
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
        Op.MSTORE(offset=0x64, value=0x9C)
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
        Op.MSTORE(offset=0x64, value=0x9D)
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
        Op.MSTORE(offset=0x64, value=0x9E)
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
        Op.MSTORE(offset=0x64, value=0x9F)
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
        Op.MSTORE(offset=0x64, value=0xA0)
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
        Op.MSTORE(offset=0x64, value=0xA1)
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
        Op.MSTORE(offset=0x64, value=0xA2)
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
        Op.MSTORE(offset=0x64, value=0xA3)
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
        Op.MSTORE(offset=0x64, value=0xA4)
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
        Op.MSTORE(offset=0x64, value=0xA5)
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
        Op.MSTORE(offset=0x64, value=0xA6)
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
        Op.MSTORE(offset=0x64, value=0xA7)
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
        Op.MSTORE(offset=0x64, value=0xA8)
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
        Op.MSTORE(offset=0x64, value=0xA9)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAA)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAB)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAC)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAD)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAE)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xAF)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB0)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB1)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB2)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB3)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB4)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xB5)
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
        Op.MSTORE(offset=0x64, value=0xB6)
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
        Op.MSTORE(offset=0x64, value=0xB7)
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
        Op.MSTORE(offset=0x64, value=0xB8)
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
        Op.MSTORE(offset=0x64, value=0xB9)
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
        Op.MSTORE(offset=0x64, value=0xBA)
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
        Op.MSTORE(offset=0x64, value=0xBB)
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
        Op.MSTORE(offset=0x64, value=0xBC)
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
        Op.MSTORE(offset=0x64, value=0xBD)
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
        Op.MSTORE(offset=0x64, value=0xBE)
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
        Op.MSTORE(offset=0x64, value=0xBF)
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
        Op.MSTORE(offset=0x64, value=0xC0)
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
        Op.MSTORE(offset=0x64, value=0xC1)
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
        Op.MSTORE(offset=0x64, value=0xC2)
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
        Op.MSTORE(offset=0x64, value=0xC3)
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
        Op.MSTORE(offset=0x64, value=0xC4)
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
        Op.MSTORE(offset=0x64, value=0xC5)
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
        Op.MSTORE(offset=0x64, value=0xC6)
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
        Op.MSTORE(offset=0x64, value=0xC7)
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
        Op.MSTORE(offset=0x64, value=0xC8)
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
        Op.MSTORE(offset=0x64, value=0xC9)
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
        Op.MSTORE(offset=0x64, value=0xCA)
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
        Op.MSTORE(offset=0x64, value=0xCB)
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
        Op.MSTORE(offset=0x64, value=0xCC)
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
        Op.MSTORE(offset=0x64, value=0xCD)
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
        Op.MSTORE(offset=0x64, value=0xCE)
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
        Op.MSTORE(offset=0x64, value=0xCF)
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
        Op.MSTORE(offset=0x64, value=0xD0)
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
        Op.MSTORE(offset=0x64, value=0xD1)
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
        Op.MSTORE(offset=0x64, value=0xD2)
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
        Op.MSTORE(offset=0x64, value=0xD3)
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
        Op.MSTORE(offset=0x64, value=0xD4)
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
        Op.MSTORE(offset=0x64, value=0xD5)
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
        Op.MSTORE(offset=0x64, value=0xD6)
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
        Op.MSTORE(offset=0x64, value=0xD7)
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
        Op.MSTORE(offset=0x64, value=0xD8)
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
        Op.MSTORE(offset=0x64, value=0xD9)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDA)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDB)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDC)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDD)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDE)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xDF)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE0)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE1)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE2)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE3)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE4)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0xE5)
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
        Op.MSTORE(offset=0x64, value=0xE6)
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
        Op.MSTORE(offset=0x64, value=0xE7)
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
        Op.MSTORE(offset=0x64, value=0xE8)
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
        Op.MSTORE(offset=0x64, value=0xE9)
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
        Op.MSTORE(offset=0x64, value=0xEA)
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
        Op.MSTORE(offset=0x64, value=0xEB)
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
        Op.MSTORE(offset=0x64, value=0xEC)
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
        Op.MSTORE(offset=0x64, value=0xED)
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
        Op.MSTORE(offset=0x64, value=0xEE)
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
        Op.MSTORE(offset=0x64, value=0xEF)
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
        Op.MSTORE(offset=0x64, value=0xF0)
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
        Op.MSTORE(offset=0x64, value=0xF1)
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
        Op.MSTORE(offset=0x64, value=0xF2)
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
        Op.MSTORE(offset=0x64, value=0xF3)
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
        Op.MSTORE(offset=0x64, value=0xF4)
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
        Op.MSTORE(offset=0x64, value=0xF5)
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
        Op.MSTORE(offset=0x64, value=0xF6)
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
        Op.MSTORE(offset=0x64, value=0xF7)
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
        Op.MSTORE(offset=0x64, value=0xF8)
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
        Op.MSTORE(offset=0x64, value=0xF9)
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
        Op.MSTORE(offset=0x64, value=0xFA)
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
        Op.MSTORE(offset=0x64, value=0xFB)
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
        Op.MSTORE(offset=0x64, value=0xFC)
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
        Op.MSTORE(offset=0x64, value=0xFD)
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
        Op.MSTORE(offset=0x64, value=0xFE)
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
        Op.MSTORE(offset=0x64, value=0xFF)
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
        Op.MSTORE(offset=0x64, value=0x100)
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
        Op.MSTORE(offset=0x64, value=0x101)
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
        Op.MSTORE(offset=0x64, value=0x102)
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
        Op.MSTORE(offset=0x64, value=0x103)
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
        Op.MSTORE(offset=0x64, value=0x104)
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
        Op.MSTORE(offset=0x64, value=0x105)
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
        Op.MSTORE(offset=0x64, value=0x106)
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
        Op.MSTORE(offset=0x64, value=0x107)
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
        Op.MSTORE(offset=0x64, value=0x108)
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
        Op.MSTORE(offset=0x64, value=0x109)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x10F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x110)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x111)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x112)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x113)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x114)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x115)
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
        Op.MSTORE(offset=0x64, value=0x116)
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
        Op.MSTORE(offset=0x64, value=0x117)
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
        Op.MSTORE(offset=0x64, value=0x118)
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
        Op.MSTORE(offset=0x64, value=0x119)
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
        Op.MSTORE(offset=0x64, value=0x11A)
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
        Op.MSTORE(offset=0x64, value=0x11B)
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
        Op.MSTORE(offset=0x64, value=0x11C)
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
        Op.MSTORE(offset=0x64, value=0x11D)
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
        Op.MSTORE(offset=0x64, value=0x11E)
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
        Op.MSTORE(offset=0x64, value=0x11F)
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
        Op.MSTORE(offset=0x64, value=0x120)
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
        Op.MSTORE(offset=0x64, value=0x121)
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
        Op.MSTORE(offset=0x64, value=0x122)
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
        Op.MSTORE(offset=0x64, value=0x123)
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
        Op.MSTORE(offset=0x64, value=0x124)
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
        Op.MSTORE(offset=0x64, value=0x125)
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
        Op.MSTORE(offset=0x64, value=0x126)
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
        Op.MSTORE(offset=0x64, value=0x127)
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
        Op.MSTORE(offset=0x64, value=0x128)
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
        Op.MSTORE(offset=0x64, value=0x129)
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
        Op.MSTORE(offset=0x64, value=0x12A)
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
        Op.MSTORE(offset=0x64, value=0x12B)
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
        Op.MSTORE(offset=0x64, value=0x12C)
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
        Op.MSTORE(offset=0x64, value=0x12D)
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
        Op.MSTORE(offset=0x64, value=0x12E)
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
        Op.MSTORE(offset=0x64, value=0x12F)
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
        Op.MSTORE(offset=0x64, value=0x130)
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
        Op.MSTORE(offset=0x64, value=0x131)
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
        Op.MSTORE(offset=0x64, value=0x132)
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
        Op.MSTORE(offset=0x64, value=0x133)
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
        Op.MSTORE(offset=0x64, value=0x134)
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
        Op.MSTORE(offset=0x64, value=0x135)
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
        Op.MSTORE(offset=0x64, value=0x136)
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
        Op.MSTORE(offset=0x64, value=0x137)
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
        Op.MSTORE(offset=0x64, value=0x138)
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
        Op.MSTORE(offset=0x64, value=0x139)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x13F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x140)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x141)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x142)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x143)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x144)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x145)
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
        Op.MSTORE(offset=0x64, value=0x146)
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
        Op.MSTORE(offset=0x64, value=0x147)
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
        Op.MSTORE(offset=0x64, value=0x148)
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
        Op.MSTORE(offset=0x64, value=0x149)
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
        Op.MSTORE(offset=0x64, value=0x14A)
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
        Op.MSTORE(offset=0x64, value=0x14B)
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
        Op.MSTORE(offset=0x64, value=0x14C)
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
        Op.MSTORE(offset=0x64, value=0x14D)
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
        Op.MSTORE(offset=0x64, value=0x14E)
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
        Op.MSTORE(offset=0x64, value=0x14F)
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
        Op.MSTORE(offset=0x64, value=0x150)
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
        Op.MSTORE(offset=0x64, value=0x151)
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
        Op.MSTORE(offset=0x64, value=0x152)
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
        Op.MSTORE(offset=0x64, value=0x153)
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
        Op.MSTORE(offset=0x64, value=0x154)
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
        Op.MSTORE(offset=0x64, value=0x155)
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
        Op.MSTORE(offset=0x64, value=0x156)
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
        Op.MSTORE(offset=0x64, value=0x157)
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
        Op.MSTORE(offset=0x64, value=0x158)
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
        Op.MSTORE(offset=0x64, value=0x159)
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
        Op.MSTORE(offset=0x64, value=0x15A)
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
        Op.MSTORE(offset=0x64, value=0x15B)
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
        Op.MSTORE(offset=0x64, value=0x15C)
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
        Op.MSTORE(offset=0x64, value=0x15D)
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
        Op.MSTORE(offset=0x64, value=0x15E)
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
        Op.MSTORE(offset=0x64, value=0x15F)
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
        Op.MSTORE(offset=0x64, value=0x160)
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
        Op.MSTORE(offset=0x64, value=0x161)
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
        Op.MSTORE(offset=0x64, value=0x162)
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
        Op.MSTORE(offset=0x64, value=0x163)
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
        Op.MSTORE(offset=0x64, value=0x164)
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
        Op.MSTORE(offset=0x64, value=0x165)
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
        Op.MSTORE(offset=0x64, value=0x166)
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
        Op.MSTORE(offset=0x64, value=0x167)
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
        Op.MSTORE(offset=0x64, value=0x168)
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
        Op.MSTORE(offset=0x64, value=0x169)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x16F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x170)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x171)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x172)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x173)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x174)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x175)
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
        Op.MSTORE(offset=0x64, value=0x176)
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
        Op.MSTORE(offset=0x64, value=0x177)
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
        Op.MSTORE(offset=0x64, value=0x178)
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
        Op.MSTORE(offset=0x64, value=0x179)
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
        Op.MSTORE(offset=0x64, value=0x17A)
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
        Op.MSTORE(offset=0x64, value=0x17B)
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
        Op.MSTORE(offset=0x64, value=0x17C)
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
        Op.MSTORE(offset=0x64, value=0x17D)
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
        Op.MSTORE(offset=0x64, value=0x17E)
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
        Op.MSTORE(offset=0x64, value=0x17F)
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
        Op.MSTORE(offset=0x64, value=0x180)
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
        Op.MSTORE(offset=0x64, value=0x181)
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
        Op.MSTORE(offset=0x64, value=0x182)
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
        Op.MSTORE(offset=0x64, value=0x183)
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
        Op.MSTORE(offset=0x64, value=0x184)
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
        Op.MSTORE(offset=0x64, value=0x185)
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
        Op.MSTORE(offset=0x64, value=0x186)
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
        Op.MSTORE(offset=0x64, value=0x187)
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
        Op.MSTORE(offset=0x64, value=0x188)
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
        Op.MSTORE(offset=0x64, value=0x189)
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
        Op.MSTORE(offset=0x64, value=0x18A)
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
        Op.MSTORE(offset=0x64, value=0x18B)
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
        Op.MSTORE(offset=0x64, value=0x18C)
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
        Op.MSTORE(offset=0x64, value=0x18D)
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
        Op.MSTORE(offset=0x64, value=0x18E)
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
        Op.MSTORE(offset=0x64, value=0x18F)
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
        Op.MSTORE(offset=0x64, value=0x190)
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
        Op.MSTORE(offset=0x64, value=0x191)
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
        Op.MSTORE(offset=0x64, value=0x192)
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
        Op.MSTORE(offset=0x64, value=0x193)
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
        Op.MSTORE(offset=0x64, value=0x194)
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
        Op.MSTORE(offset=0x64, value=0x195)
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
        Op.MSTORE(offset=0x64, value=0x196)
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
        Op.MSTORE(offset=0x64, value=0x197)
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
        Op.MSTORE(offset=0x64, value=0x198)
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
        Op.MSTORE(offset=0x64, value=0x199)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19A)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19B)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19C)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19D)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19E)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x19F)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A0)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A1)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A2)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A3)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A4)
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
        + Op.POP(
            Op.CALLCODE(
                gas=0x493E0,
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
        Op.MSTORE(offset=0x64, value=0x1A5)
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
        Op.MSTORE(offset=0x64, value=0x1A6)
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
        Op.MSTORE(offset=0x64, value=0x1A7)
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
        Op.MSTORE(offset=0x64, value=0x1A8)
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
        Op.MSTORE(offset=0x64, value=0x1A9)
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

    if d == 0:
        initcode = (
            Op.MSTORE(offset=0x64, value=0x0)
            + Op.POP(
                Op.STATICCALL(gas=gas, address=change_contract, args_size=0x20)
            )
            + Op.CALL(gas=gas * 2, address=contract_4)
            + Op.STOP
        )
        assert initcode == tx_data[d]
    else:
        idx = 0x0 + d - 1  # 4-call index

        call_1_op = dim0_types[idx // 576]
        call_2_op = call_types[(idx // 48) % 12 // 3]
        call_2_contract = contracts[(idx // 48) % 12 % 3]
        call_3_op = dim2_types[(idx // 12) % 4]
        call_4_op = call_types[idx % 12 // 3]
        call_4_contract = contracts[idx % 12 % 3]

        initcode = (
            Op.MSTORE(offset=0x64, value=0x0 + d)
            + Op.POP(
                call_1_op(gas=gas, address=change_contract, args_size=0x20)
            )
            + Op.POP(call_2_op(gas=gas, address=call_2_contract))
            + Op.POP(
                call_3_op(gas=gas, address=change_contract, args_size=0x20)
            )
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
