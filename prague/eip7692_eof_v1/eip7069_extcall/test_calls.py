"""
test calls across EOF and Legacy
"""
import itertools

import pytest

from ethereum_test_tools import (
    EOA,
    Account,
    Address,
    Alloc,
    Environment,
    StateTestFiller,
    Storage,
    Transaction,
)
from ethereum_test_tools.eof.v1 import Container, Section
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .. import EOF_FORK_NAME
from .spec import (
    EXTCALL_FAILURE,
    EXTCALL_REVERT,
    EXTCALL_SUCCESS,
    LEGACY_CALL_FAILURE,
    LEGACY_CALL_SUCCESS,
)

pytestmark = pytest.mark.valid_from(EOF_FORK_NAME)
REFERENCE_SPEC_GIT_PATH = "EIPS/eip-3540.md"
REFERENCE_SPEC_VERSION = "2f013de4065babde7c02f84a2ce9864a3c5bfbd3"

"""Storage addresses for common testing fields"""
_slot = itertools.count(1)
slot_code_worked = next(_slot)
slot_call_result = next(_slot)
slot_returndata = next(_slot)
slot_returndatasize = next(_slot)
slot_caller = next(_slot)
slot_returndatasize_before_clear = next(_slot)
slot_max_depth = next(_slot)
slot_last_slot = next(_slot)

"""Storage values for common testing fields"""
value_code_worked = 0x2015
value_returndata_magic = b"\x42"


contract_eof_sstore = Container(
    sections=[
        Section.Code(
            code=Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP,
        )
    ]
)


@pytest.fixture
def sender(pre: Alloc) -> EOA:
    """
    The sender of the transaction
    """
    return pre.fund_eoa()


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
def test_legacy_calls_eof_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test legacy contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Op.SSTORE(
        slot_call_result, opcode(address=destination_contract_address)
    ) + Op.SSTORE(slot_code_worked, value_code_worked)

    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = Storage(
        {
            slot_code_worked: value_code_worked,  # type: ignore
            slot_call_result: LEGACY_CALL_SUCCESS,  # type: ignore
        }
    )
    destination_storage = Storage()

    if opcode == Op.CALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.DELEGATECALL:
        calling_storage[slot_caller] = sender
    elif opcode == Op.CALLCODE:
        calling_storage[slot_caller] = calling_contract_address
    elif opcode == Op.STATICCALL:
        calling_storage[slot_call_result] = LEGACY_CALL_FAILURE

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.DELEGATECALL,
        Op.CALLCODE,
        Op.STATICCALL,
    ],
)
def test_legacy_calls_eof_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test legacy contracts calling EOF contracts that only return data"""
    env = Environment()
    destination_contract_code = Container(
        sections=[
            Section.Code(
                code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                + Op.RETURN(0, len(value_returndata_magic)),
            )
        ]
    )
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = (
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
        + Op.RETURNDATACOPY(31, 0, 1)
        + Op.SSTORE(slot_returndata, Op.MLOAD(0))
        + Op.SSTORE(slot_code_worked, value_code_worked)
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: LEGACY_CALL_SUCCESS,  # type: ignore
        slot_returndatasize: len(value_returndata_magic),  # type: ignore
        slot_returndata: value_returndata_magic,  # type: ignore
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_eof_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling EOF contracts that use SSTORE"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = Storage(
        {
            slot_code_worked: value_code_worked,  # type: ignore
            slot_call_result: EXTCALL_SUCCESS,  # type: ignore
        }
    )
    destination_storage = Storage()

    if opcode == Op.EXTCALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.EXTDELEGATECALL:
        calling_storage[slot_caller] = sender
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = EXTCALL_FAILURE

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_eof_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling EOF contracts that return data"""
    env = Environment()
    destination_contract_code = Container(
        sections=[
            Section.Code(
                code=Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big"))
                + Op.RETURN(0, 32),
            )
        ]
    )
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: EXTCALL_SUCCESS,  # type: ignore
        slot_returndatasize: 0x20,  # type: ignore
        slot_returndata: value_returndata_magic
        + b"\0" * (0x20 - len(value_returndata_magic)),  # type: ignore
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_legacy_sstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling Legacy contracts that use SSTORE"""
    env = Environment()
    destination_contract_code = Op.SSTORE(slot_caller, Op.CALLER()) + Op.STOP
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: EXTCALL_SUCCESS,  # type: ignore
    }
    destination_storage = {}

    if opcode == Op.EXTCALL:
        destination_storage[slot_caller] = calling_contract_address
    elif opcode == Op.EXTDELEGATECALL:
        # EOF delegate call to legacy is a light failure by rule
        calling_storage[slot_call_result] = EXTCALL_REVERT
    elif opcode == Op.EXTSTATICCALL:
        calling_storage[slot_call_result] = EXTCALL_FAILURE

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage=destination_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_legacy_mstore(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calling Legacy contracts that return data"""
    env = Environment()
    destination_contract_code = Op.MSTORE8(
        0, int.from_bytes(value_returndata_magic, "big")
    ) + Op.RETURN(0, 32)
    destination_contract_address = pre.deploy_contract(destination_contract_code)

    caller_contract = Container(
        sections=[
            Section.Code(
                code=Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
                + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
                + Op.SSTORE(slot_returndata, Op.RETURNDATALOAD(0))
                + Op.SSTORE(slot_code_worked, value_code_worked)
                + Op.STOP,
            )
        ]
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,  # type: ignore
        slot_call_result: EXTCALL_SUCCESS,  # type: ignore
        slot_returndatasize: 0x20,  # type: ignore
        slot_returndata: value_returndata_magic
        + b"\0" * (0x20 - len(value_returndata_magic)),  # type: ignore
    }

    if opcode == Op.EXTDELEGATECALL:
        # EOF delegate call to legacy is a light failure by rule
        calling_storage[slot_call_result] = EXTCALL_REVERT
        calling_storage[slot_returndatasize] = 0
        calling_storage[slot_returndata] = 0

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
@pytest.mark.parametrize(
    "destination_opcode",
    [Op.REVERT, Op.INVALID],
)
@pytest.mark.parametrize("destination_is_eof", [True, False])
def test_eof_calls_revert_abort(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    destination_opcode: Op,
    destination_is_eof: bool,
):
    """Test EOF contracts calling contracts that revert or abort"""
    env = Environment()

    destination_contract_address = pre.deploy_contract(
        Container.Code(destination_opcode(offset=0, size=0))
        if destination_is_eof
        else destination_opcode(offset=0, size=0)
    )

    caller_contract = Container.Code(
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        slot_call_result: EXTCALL_REVERT
        if destination_opcode == Op.REVERT
        or (opcode == Op.EXTDELEGATECALL and not destination_is_eof)
        else EXTCALL_FAILURE,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        destination_contract_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
    ],
)
@pytest.mark.parametrize("fail_opcode", [Op.REVERT, Op.INVALID])
def test_eof_calls_eof_then_fails(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    fail_opcode: Op,
):
    """Test EOF contracts calling EOF contracts and failing after the call"""
    env = Environment()
    destination_contract_address = pre.deploy_contract(contract_eof_sstore)

    caller_contract = Container.Code(
        Op.SSTORE(slot_call_result, opcode(address=destination_contract_address))
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + fail_opcode(offset=0, size=0),
    )
    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    post = {
        calling_contract_address: Account(storage=Storage()),
        destination_contract_address: Account(storage=Storage()),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
@pytest.mark.parametrize(
    "target_account_type",
    (
        "empty",
        "EOA",
        "LegacyContract",
        "EOFContract",
        "LegacyContractInvalid",
        "EOFContractInvalid",
    ),
    ids=lambda x: x,
)
@pytest.mark.parametrize("value", [0, 1])
def test_eof_calls_clear_return_buffer(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    target_account_type: str,
    value: int,
):
    """Test EOF contracts calling clears returndata buffer"""
    env = Environment()
    filling_contract_code = Container.Code(
        Op.MSTORE8(0, int.from_bytes(value_returndata_magic, "big")) + Op.RETURN(0, 32),
    )
    filling_callee_address = pre.deploy_contract(filling_contract_code)

    match target_account_type:
        case "empty":
            target_address = b"\x78" * 20
        case "EOA":
            target_address = pre.fund_eoa()
        case "LegacyContract":
            target_address = pre.deploy_contract(
                code=Op.STOP,
            )
        case "EOFContract":
            target_address = pre.deploy_contract(
                code=Container.Code(Op.STOP),
            )
        case "LegacyContractInvalid":
            target_address = pre.deploy_contract(
                code=Op.INVALID,
            )
        case "EOFContractInvalid":
            target_address = pre.deploy_contract(
                code=Container.Code(Op.INVALID),
            )

    caller_contract = Container.Code(
        # First fill the return buffer and sanity check
        Op.EXTCALL(filling_callee_address, 0, 0, 0)
        + Op.SSTORE(slot_returndatasize_before_clear, Op.RETURNDATASIZE)
        # Then call something that doesn't return and check returndata cleared
        + opcode(address=target_address, value=value)
        + Op.SSTORE(slot_returndatasize, Op.RETURNDATASIZE)
        + Op.SSTORE(slot_code_worked, value_code_worked)
        + Op.STOP,
    )

    calling_contract_address = pre.deploy_contract(caller_contract)

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        # Sanity check
        slot_returndatasize_before_clear: 0x20,
        slot_returndatasize: 0,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        filling_callee_address: Account(storage={}),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.CALL,
        Op.EXTCALL,
    ],
)
def test_eof_calls_static_flag_with_value(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """Test EOF contracts calls handle static flag and sending value correctly"""
    env = Environment()

    noop_callee_address = pre.deploy_contract(Container.Code(Op.STOP))

    failing_contract_code = opcode(address=noop_callee_address, value=1) + Op.STOP
    failing_contract_address = pre.deploy_contract(
        Container.Code(
            failing_contract_code,
        )
        if opcode == Op.EXTCALL
        else failing_contract_code
    )

    calling_contract_address = pre.deploy_contract(
        Container.Code(
            Op.SSTORE(slot_call_result, Op.EXTSTATICCALL(address=failing_contract_address))
            + Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.STOP
        )
    )
    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=5_000_000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        slot_call_result: EXTCALL_FAILURE,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


min_retained_gas = 2300
min_callee_gas = 5000


@pytest.mark.parametrize(
    ["opcode", "extra_gas_value_transfer", "value"],
    [
        [Op.EXTCALL, 0, 0],
        [Op.EXTCALL, 9_000, 1],
        [Op.EXTSTATICCALL, 0, 0],
        [Op.EXTDELEGATECALL, 0, 0],
    ],
    ids=["extcall_without_value", "extcall_with_value", "extstaticcall", "extdelegatecall"],
)
@pytest.mark.parametrize(
    ["extra_gas_limit", "reverts"],
    [
        [0, False],
        [min_retained_gas, False],
        [min_callee_gas, False],
        [min_retained_gas + min_callee_gas, True],
    ],
    ids=["no_allowances", "only_retained", "only_callee", "both_allowances"],
)
def test_eof_calls_min_callee_gas(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
    extra_gas_value_transfer: int,
    value: int,
    extra_gas_limit: int,
    reverts: bool,
):
    """
    Test EOF contracts calls do light failure when retained/callee gas is not enough.

    Premise of the test is that there exists a range of `gas_limit` values, which are enough
    for all instructions to execute, but call's returned value is 1, meaning not enough for gas
    allowances (MIN_RETAINED_GAS and MIN_CALLEE_GAS) - ones marked with `reverts==False`.

    Once we provide both allowances, the RJUMPI condition is no longer met and `reverts==True`.
    """
    env = Environment()

    noop_callee_address = pre.deploy_contract(Container.Code(Op.STOP))

    revert_block = Op.REVERT(0, 0)
    calling_contract_address = pre.deploy_contract(
        Container.Code(
            Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.EQ(opcode(address=noop_callee_address, value=value), EXTCALL_REVERT)
            # If the return code isn't 1, it means gas was enough to cover the allowances.
            + Op.RJUMPI[len(revert_block)]
            + revert_block
            + Op.STOP
        ),
        balance=value,
    )

    # `no_oog_gas` is minimum amount of gas_limit which makes the transaction not go oog.
    push_operations = 3 + len(opcode.kwargs)  # type: ignore
    no_oog_gas = (
        21_000
        + 20_000  # SSTORE
        + 2_100  # SSTORE COLD_SLOAD_COST
        + push_operations * 3  # PUSH operations
        + 100  # WARM_STORAGE_READ_COST
        + 2500  # COLD_ACCOUNT_ACCESS - WARM_STORAGE_READ_COST
        + extra_gas_value_transfer
        + 4  # RJUMPI
        + 3  # EQ
    )

    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=no_oog_gas + extra_gas_limit,
        data="",
    )

    calling_storage = {
        slot_code_worked: 0 if reverts else value_code_worked,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "balance", [0, 1, 2, pytest.param(2**256 - 1, marks=pytest.mark.pre_alloc_modify)]
)
@pytest.mark.parametrize("value", [0, 1, 2, 2**256 - 1])
def test_eof_calls_with_value(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    balance: int,
    value: int,
):
    """Test EOF contracts calls handle value calls with and without enough balance"""
    env = Environment()

    noop_callee_address = pre.deploy_contract(Container.Code(Op.STOP))

    calling_contract_address = pre.deploy_contract(
        Container.Code(
            Op.SSTORE(slot_call_result, Op.EXTCALL(address=noop_callee_address, value=value))
            + Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.STOP
        ),
        balance=balance,
    )
    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=50000000,
        data="",
    )

    calling_storage = {
        slot_code_worked: value_code_worked,
        slot_call_result: EXTCALL_REVERT if balance < value else EXTCALL_SUCCESS,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
        noop_callee_address: Account(balance=0 if balance < value else value),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.parametrize(
    "opcode",
    [
        Op.EXTCALL,
        Op.EXTDELEGATECALL,
        Op.EXTSTATICCALL,
    ],
)
def test_eof_calls_msg_depth(
    state_test: StateTestFiller,
    pre: Alloc,
    sender: EOA,
    opcode: Op,
):
    """
    Test EOF contracts calls handle msg depth limit correctly (1024).
    NOTE: due to block gas limit and the 63/64th rule this limit is unlikely to be hit
          on mainnet.
    """
    # Not a precise gas_limit formula, but enough to exclude risk of gas causing the failure.
    gas_limit = int(200000 * (64 / 63) ** 1024)
    env = Environment(gas_limit=gas_limit)

    # Flow of the test:
    # `callee_code` is recursively calling itself, passing msg depth as calldata
    # (kept with the `MSTORE(0, ADD(...))`). When maximum msg depth is reached
    # the call fails and starts returning. The deep-most frame returns:
    #   - current reached msg depth (expected to be the maximum 1024), with the
    #     `MSTORE(32, ADD(...))`
    #   - the respective return code of the EXT*CALL (expected to be 1 - light failure), with the
    #     `MSTORE(64, NOOP)`. Note the `NOOP` is just to appease the `Op.MSTORE` call, the return
    #     code value is actually coming from the `Op.DUP1`
    # When unwinding the msg call stack, the intermediate frames return whatever the deeper callee
    # returned with the `RETURNDATACOPY` instruction.

    # Memory offsets layout:
    # - 0  - input - msg depth
    # - 32 - output - msg depth
    # - 64 - output - call result
    returndatacopy_block = Op.RETURNDATACOPY(32, 0, 64) + Op.RETURN(32, 64)
    deep_most_result_block = (
        Op.MSTORE(32, Op.ADD(Op.CALLDATALOAD(0), 1)) + Op.MSTORE(64, Op.NOOP) + Op.RETURN(32, 64)
    )
    rjump_offset = len(returndatacopy_block)

    callee_code = Container.Code(
        # current stack depth in memory bytes 0-31
        Op.MSTORE(0, Op.ADD(Op.CALLDATALOAD(0), 1))
        # pass it along deeper as calldata
        + opcode(address=Op.ADDRESS, args_size=32)
        # duplicate return code for the `returndatacopy_block` below
        + Op.DUP1
        # if return code was:
        #  - 1, we're in the deep-most frame, `deep_most_result_block` returns the actual result
        #  - 0, we're in an intermediate frame, `returndatacopy_block` only passes on the result
        + Op.RJUMPI[rjump_offset]
        + returndatacopy_block
        + deep_most_result_block
    )

    callee_address = pre.deploy_contract(callee_code)

    calling_contract_address = pre.deploy_contract(
        Container.Code(
            Op.MSTORE(0, Op.CALLDATALOAD(0))
            + Op.EXTCALL(address=callee_address, args_size=32)
            + Op.SSTORE(slot_max_depth, Op.RETURNDATALOAD(0))
            + Op.SSTORE(slot_call_result, Op.RETURNDATALOAD(32))
            + Op.SSTORE(slot_code_worked, value_code_worked)
            + Op.STOP
        )
    )
    tx = Transaction(
        sender=sender,
        to=Address(calling_contract_address),
        gas_limit=gas_limit,
        data="",
    )

    calling_storage = {
        slot_max_depth: 1024,
        slot_code_worked: value_code_worked,
        slot_call_result: EXTCALL_REVERT,
    }

    post = {
        calling_contract_address: Account(storage=calling_storage),
    }

    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )
