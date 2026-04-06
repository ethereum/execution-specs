"""
Sstore 1 -> {calltype} -> change to {0, 1, 2} |-> {calltype} -> {non,...

Ported from:
state_tests/stTimeConsuming/sstore_combinations_initial11_2_ParisFiller.json

@manually-enhanced: Do not overwrite. This test has been manually reviewed and
enhanced.
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
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
        "state_tests/stTimeConsuming/sstore_combinations_initial11_2_ParisFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d",
    range(453),
    ids=lambda d: f"d{d}",
)
@pytest.mark.pre_alloc_mutable
def test_sstore_combinations_initial11_2_paris(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
) -> None:
    """Sstore 1 -> {calltype} -> change to {0, 1, 2} |-> {calltype} ->..."""
    contract_0 = Address(0xB000000000000000000000000000000000000000)
    contract_1 = Address(0xB100000000000000000000000000000000000000)
    contract_2 = Address(0xB200000000000000000000000000000000000000)
    contract_3 = Address(0x1000000000000000000000000000000000000000)
    contract_4 = Address(0x2000000000000000000000000000000000000000)
    contract_5 = Address(0x3000000000000000000000000000000000000000)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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
        code=sum(
            Op.SSTORE(key=i, value=0x1) + Op.SSTORE(key=i, value=0x0)
            for i in range(0x1, 0x10 + 1)
        )
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

    # Combinatorial initcode generator
    # 1728 entries = 3 x 12 x 4 x 12 (dims: outer to inner)
    #   dim0: 1st change call type (3) - CALL, CALLCODE, DELEGATECALL
    #   dim1: middle action 1 (12) - {CALL,CALLCODE,DELEGATECALL,STATICCALL} x {c3,c4,c5}  # noqa: E501
    #   dim2: 2nd change call type (4) - STATICCALL, CALL, CALLCODE, DELEGATECALL  # noqa: E501
    #   dim3: middle action 2 (12) - {CALL,CALLCODE,DELEGATECALL,STATICCALL} x {c3,c4,c5}  # noqa: E501
    gas = 0x493E0
    dim0_types = [Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
    dim2_types = [Op.STATICCALL, Op.CALL, Op.CALLCODE, Op.DELEGATECALL]
    call_types = [Op.CALL, Op.CALLCODE, Op.DELEGATECALL, Op.STATICCALL]
    contracts = [contract_3, contract_4, contract_5]
    change_contract = contract_1

    idx = 0x4FC + d - 1  # 4-call index

    call_1_op = dim0_types[idx // 576]
    call_2_op = call_types[(idx // 48) % 12 // 3]
    call_2_contract = contracts[(idx // 48) % 12 % 3]
    call_3_op = dim2_types[(idx // 12) % 4]
    call_4_op = call_types[idx % 12 // 3]
    call_4_contract = contracts[idx % 12 % 3]

    initcode = (
        Op.MSTORE(offset=0x64, value=0x4FC + d)
        + Op.POP(call_1_op(gas=gas, address=change_contract, args_size=0x20))
        + Op.POP(call_2_op(gas=gas, address=call_2_contract))
        + Op.POP(call_3_op(gas=gas, address=change_contract, args_size=0x20))
        + Op.POP(call_4_op(gas=gas, address=call_4_contract))
        + Op.CALL(gas=gas * 2, address=contract_4)
        + Op.STOP
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=initcode,
        gas_limit=2_000_000,
        value=1,
    )

    post = {
        contract_4: Account(storage={1: 1}),
        compute_create_address(address=sender, nonce=0): Account(nonce=1),
    }

    state_test(pre=pre, post=post, tx=tx)
