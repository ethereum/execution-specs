"""abstract: Test identity precompile output size."""

from typing import Tuple

import pytest

from ethereum_test_base_types.composite_types import Storage
from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools import Opcodes as Op

from .common import CallArgs, generate_identity_call_bytecode


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentitiy_0Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentitiy_1Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_1_nonzeroValueFiller.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_2Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_3Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_4Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_4_gas17Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_4_gas18Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentitiy_0Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentitiy_1Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_1_nonzeroValueFiller.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_2Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_3Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_4Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_4_gas17Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_4_gas18Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1344"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize("call_type", [Op.CALL, Op.CALLCODE])
@pytest.mark.parametrize(
    [
        "call_args",
        "memory_values",
        "call_succeeds",
    ],
    [
        pytest.param(CallArgs(gas=0xFF), (0x1,), True, id="identity_0"),
        pytest.param(
            CallArgs(args_size=0x0),
            (0x0,),
            True,
            id="identity_1",
        ),
        pytest.param(
            CallArgs(gas=0x30D40, value=0x1, args_size=0x0),
            None,
            False,
            id="identity_1_nonzerovalue",
        ),
        pytest.param(
            CallArgs(args_size=0x25),
            (0xF34578907F,),
            True,
            id="identity_2",
        ),
        pytest.param(
            CallArgs(args_size=0x25),
            (0xF34578907F,),
            True,
            id="identity_3",
        ),
        pytest.param(
            CallArgs(gas=0x64),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,),
            True,
            id="identity_4",
        ),
        pytest.param(
            CallArgs(gas=0x11),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,),
            False,
            id="identity_4_insufficient_gas",
        ),
        pytest.param(
            CallArgs(gas=0x12),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,),
            True,
            id="identity_4_exact_gas",
        ),
    ],
)
def test_call_identity_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    call_type: Op,
    call_args: CallArgs,
    memory_values: Tuple[int, ...],
    call_succeeds: bool,
    tx_gas_limit: int,
):
    """Test identity precompile RETURNDATA is sized correctly based on the input size."""
    env = Environment()
    storage = Storage()

    contract_bytecode = generate_identity_call_bytecode(
        storage,
        call_type,
        memory_values,
        call_args,
        call_succeeds,
    )

    account = pre.deploy_contract(
        contract_bytecode,
        storage=storage.canary(),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=tx_gas_limit,
    )

    post = {account: Account(storage=storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CALLCODEIdentity_5Filler.json",
        "https://github.com/ethereum/tests/blob/v17.1/src/GeneralStateTestsFiller/stPreCompiledContracts2/CallIdentity_5Filler.json",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1344"],
)
@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize("call_type", [Op.CALL, Op.CALLCODE])
@pytest.mark.parametrize(
    [
        "call_args",
        "memory_values",
        "call_succeeds",
    ],
    [
        pytest.param(
            CallArgs(gas=0x258, args_size=0xF4240),
            (0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,),
            False,
            id="identity_5",
        ),
        pytest.param(
            CallArgs(gas=0x258, ret_size=0x40),
            (
                0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF,
                0x1234,
            ),
            True,
            id="identity_6",
        ),
    ],
)
@pytest.mark.parametrize("tx_gas_limit", [10_000_000])
def test_call_identity_precompile_large_params(
    state_test: StateTestFiller,
    pre: Alloc,
    call_type: Op,
    call_args: CallArgs,
    memory_values: Tuple[int, ...],
    call_succeeds: bool,
    tx_gas_limit: int,
):
    """Test identity precompile when out of gas occurs."""
    env = Environment()
    storage = Storage()

    contract_bytecode = generate_identity_call_bytecode(
        storage,
        call_type,
        memory_values,
        call_args,
        call_succeeds,
    )

    account = pre.deploy_contract(
        contract_bytecode,
        storage=storage.canary(),
    )

    tx = Transaction(
        to=account,
        sender=pre.fund_eoa(),
        gas_limit=tx_gas_limit,
    )

    post = {account: Account(storage=storage)}

    state_test(env=env, pre=pre, post=post, tx=tx)
