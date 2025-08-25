"""
abstract: Tests [EIP-3651: Warm COINBASE](https://eips.ethereum.org/EIPS/eip-3651)
    Tests for [EIP-3651: Warm COINBASE](https://eips.ethereum.org/EIPS/eip-3651).

note: Tests ported from:
    - [ethereum/tests/pull/1082](https://github.com/ethereum/tests/pull/1082).
"""

import pytest

from ethereum_test_forks import Fork, Shanghai
from ethereum_test_tools import (
    Account,
    Address,
    Alloc,
    Bytecode,
    CodeGasMeasure,
    Environment,
    StateTestFiller,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .spec import ref_spec_3651

REFERENCE_SPEC_GIT_PATH = ref_spec_3651.git_path
REFERENCE_SPEC_VERSION = ref_spec_3651.version

# Amount of gas required to make a call to a warm account.
# Calling a cold account with this amount of gas results in exception.
GAS_REQUIRED_CALL_WARM_ACCOUNT = 100


@pytest.mark.valid_from("Shanghai")
@pytest.mark.parametrize(
    "use_sufficient_gas",
    [True, False],
    ids=["sufficient_gas", "insufficient_gas"],
)
@pytest.mark.parametrize(
    "opcode,contract_under_test_code,call_gas_exact",
    [
        (
            "call",
            Op.POP(Op.CALL(0, Op.COINBASE, 0, 0, 0, 0, 0)),
            # Extra gas: COINBASE + 4*PUSH1 + 2*DUP1 + POP
            GAS_REQUIRED_CALL_WARM_ACCOUNT + 22,
        ),
        (
            "callcode",
            Op.POP(Op.CALLCODE(0, Op.COINBASE, 0, 0, 0, 0, 0)),
            # Extra gas: COINBASE + 4*PUSH1 + 2*DUP1 + POP
            GAS_REQUIRED_CALL_WARM_ACCOUNT + 22,
        ),
        (
            "delegatecall",
            Op.POP(Op.DELEGATECALL(0, Op.COINBASE, 0, 0, 0, 0)),
            # Extra: COINBASE + 3*PUSH1 + 2*DUP1 + POP
            GAS_REQUIRED_CALL_WARM_ACCOUNT + 19,
        ),
        (
            "staticcall",
            Op.POP(Op.STATICCALL(0, Op.COINBASE, 0, 0, 0, 0)),
            # Extra: COINBASE + 3*PUSH1 + 2*DUP1 + POP
            GAS_REQUIRED_CALL_WARM_ACCOUNT + 19,
        ),
    ],
    ids=["CALL", "CALLCODE", "DELEGATECALL", "STATICCALL"],
)
def test_warm_coinbase_call_out_of_gas(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    post: Alloc,
    sender: Address,
    fork: Fork,
    opcode: str,
    contract_under_test_code: Bytecode,
    call_gas_exact: int,
    use_sufficient_gas: bool,
):
    """
    Test that the coinbase is warm by accessing the COINBASE with each
    of the following opcodes.

    - CALL
    - CALLCODE
    - DELEGATECALL
    - STATICCALL
    """
    contract_under_test_address = pre.deploy_contract(contract_under_test_code)

    if not use_sufficient_gas:
        call_gas_exact -= 1

    caller_code = Op.SSTORE(
        0,
        Op.CALL(call_gas_exact, contract_under_test_address, 0, 0, 0, 0, 0),
    )
    caller_address = pre.deploy_contract(caller_code)

    tx = Transaction(
        ty=0x0,
        chain_id=0x01,
        nonce=0,
        to=caller_address,
        gas_limit=100_000,
        gas_price=10,
        sender=sender,
    )

    if use_sufficient_gas and fork >= Shanghai:
        post[caller_address] = Account(
            storage={
                # On shanghai and beyond, calls with only 100 gas to
                # coinbase will succeed.
                0: 1,
            }
        )
    else:
        post[caller_address] = Account(
            storage={
                # Before shanghai, calls with only 100 gas to
                # coinbase will fail.
                0: 0,
            }
        )

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        tag="opcode_" + opcode,
    )


# List of opcodes that are affected by EIP-3651
gas_measured_opcodes = [
    (
        "EXTCODESIZE",
        CodeGasMeasure(
            code=Op.EXTCODESIZE(Op.COINBASE),
            overhead_cost=2,
            extra_stack_items=1,
        ),
    ),
    (
        "EXTCODECOPY",
        CodeGasMeasure(
            code=Op.EXTCODECOPY(Op.COINBASE, 0, 0, 0),
            overhead_cost=2 + 3 + 3 + 3,
        ),
    ),
    (
        "EXTCODEHASH",
        CodeGasMeasure(
            code=Op.EXTCODEHASH(Op.COINBASE),
            overhead_cost=2,
            extra_stack_items=1,
        ),
    ),
    (
        "BALANCE",
        CodeGasMeasure(
            code=Op.BALANCE(Op.COINBASE),
            overhead_cost=2,
            extra_stack_items=1,
        ),
    ),
    (
        "CALL",
        CodeGasMeasure(
            code=Op.CALL(0xFF, Op.COINBASE, 0, 0, 0, 0, 0),
            overhead_cost=3 + 2 + 3 + 3 + 3 + 3 + 3,
            extra_stack_items=1,
        ),
    ),
    (
        "CALLCODE",
        CodeGasMeasure(
            code=Op.CALLCODE(0xFF, Op.COINBASE, 0, 0, 0, 0, 0),
            overhead_cost=3 + 2 + 3 + 3 + 3 + 3 + 3,
            extra_stack_items=1,
        ),
    ),
    (
        "DELEGATECALL",
        CodeGasMeasure(
            code=Op.DELEGATECALL(0xFF, Op.COINBASE, 0, 0, 0, 0),
            overhead_cost=3 + 2 + 3 + 3 + 3 + 3,
            extra_stack_items=1,
        ),
    ),
    (
        "STATICCALL",
        CodeGasMeasure(
            code=Op.STATICCALL(0xFF, Op.COINBASE, 0, 0, 0, 0),
            overhead_cost=3 + 2 + 3 + 3 + 3 + 3,
            extra_stack_items=1,
        ),
    ),
]


@pytest.mark.valid_from("Berlin")  # these tests fill for fork >= Berlin
@pytest.mark.parametrize(
    "opcode,code_gas_measure",
    gas_measured_opcodes,
    ids=[i[0] for i in gas_measured_opcodes],
)
def test_warm_coinbase_gas_usage(
    state_test: StateTestFiller,
    env: Environment,
    pre: Alloc,
    sender: Address,
    fork: Fork,
    opcode: str,
    code_gas_measure: Bytecode,
):
    """
    Test the gas usage of opcodes affected by assuming a warm coinbase.

    - EXTCODESIZE
    - EXTCODECOPY
    - EXTCODEHASH
    - BALANCE
    - CALL
    - CALLCODE
    - DELEGATECALL
    - STATICCALL
    """
    measure_address = pre.deploy_contract(
        code=code_gas_measure,
    )

    if fork >= Shanghai:
        expected_gas = GAS_REQUIRED_CALL_WARM_ACCOUNT  # Warm account access cost after EIP-3651
    else:
        expected_gas = 2600  # Cold account access cost before EIP-3651

    tx = Transaction(
        ty=0x0,
        chain_id=0x01,
        nonce=0,
        to=measure_address,
        gas_limit=100_000,
        gas_price=10,
        sender=sender,
    )

    post = {
        measure_address: Account(
            storage={
                0x00: expected_gas,
            }
        )
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
        tag="opcode_" + opcode.lower(),
    )
