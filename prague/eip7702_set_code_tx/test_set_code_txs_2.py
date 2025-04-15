"""A state test for [EIP-7702 SetCodeTX](https://eips.ethereum.org/EIPS/eip-7702)."""

from enum import Enum, IntEnum

import pytest

from ethereum_test_forks import Fork, GasCosts
from ethereum_test_tools import (
    AccessList,
    Account,
    Alloc,
    AuthorizationTuple,
    Block,
    BlockchainTestFiller,
    Bytes,
    Case,
    Conditional,
    Environment,
    Hash,
    StateTestFiller,
    Storage,
    Switch,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op
from ethereum_test_types.eof.v1 import Container, Section
from ethereum_test_vm import Macros

from .spec import Spec, ref_spec_7702

REFERENCE_SPEC_GIT_PATH = ref_spec_7702.git_path
REFERENCE_SPEC_VERSION = ref_spec_7702.version


@pytest.mark.valid_from("Prague")
def test_pointer_contract_pointer_loop(state_test: StateTestFiller, pre: Alloc):
    """
    Tx -> call -> pointer A -> contract A -> pointer B -> contract loop C.

    Call pointer that goes more level of depth to call a contract loop
    Loop is created only if pointers are set with auth tuples
    """
    env = Environment()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    pointer_b = pre.fund_eoa()

    storage: Storage = Storage()
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(1, "contract_a_worked"), 0x1)
        + Op.CALL(gas=1_000_000, address=pointer_b)
        + Op.STOP,
    )

    storage_loop: Storage = Storage()
    contract_worked = storage_loop.store_next(112, "contract_loop_worked")
    contract_loop = pre.deploy_contract(
        code=Op.SSTORE(contract_worked, Op.ADD(1, Op.SLOAD(0)))
        + Op.CALL(gas=1_000_000, address=pointer_a)
        + Op.STOP,
    )
    tx = Transaction(
        to=pointer_a,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_a,
            ),
            AuthorizationTuple(
                address=contract_loop,
                nonce=0,
                signer=pointer_b,
            ),
        ],
    )

    post = {
        pointer_a: Account(storage=storage),
        pointer_b: Account(storage=storage_loop),
    }
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
def test_pointer_to_pointer(state_test: StateTestFiller, pre: Alloc):
    """
    Tx -> call -> pointer A -> pointer B.

    Direct call from pointer to pointer is OOG
    """
    env = Environment()

    storage: Storage = Storage()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    pointer_b = pre.fund_eoa()

    contract_a = pre.deploy_contract(
        code=Op.SSTORE(storage.store_next(0, "contract_a_worked"), 0x1)
        + Op.CALL(gas=1_000_000, address=pointer_b)
        + Op.STOP,
    )

    tx = Transaction(
        to=pointer_a,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=pointer_b,
                nonce=0,
                signer=pointer_a,
            ),
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_b,
            ),
        ],
    )
    post = {pointer_a: Account(storage=storage)}
    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.valid_from("Prague")
def test_pointer_normal(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """
    Tx -> call -> pointer A -> contract
    Other normal tx can interact with previously assigned pointers.
    """
    env = Environment()

    storage: Storage = Storage()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    slot_worked = storage.store_next(3, "contract_a_worked")
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(slot_worked, Op.ADD(1, Op.SLOAD(slot_worked))) + Op.STOP,
    )

    tx = Transaction(
        to=pointer_a,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    # Other normal tx can interact with previously assigned pointers
    tx_2 = Transaction(
        to=pointer_a,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
    )

    # Event from another block
    tx_3 = Transaction(
        to=pointer_a,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
    )

    post = {pointer_a: Account(storage=storage)}
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[Block(txs=[tx, tx_2]), Block(txs=[tx_3])],
    )


@pytest.mark.valid_from("Prague")
def test_pointer_measurements(blockchain_test: BlockchainTestFiller, pre: Alloc):
    """
    Check extcode* operations on pointer before and after pointer is set
    Check context opcode results when called under pointer call
    Opcodes have context of an original pointer account (balance, storage).
    """
    env = Environment()

    sender = pre.fund_eoa()
    pointer = pre.fund_eoa(amount=100)

    storage_normal: Storage = Storage()
    storage_pointer: Storage = Storage()
    storage_pointer_code: Storage = Storage()  # this storage will be applied to pointer address
    pointer_code = pre.deploy_contract(
        balance=200,
        code=Op.SSTORE(storage_pointer_code.store_next(pointer, "address"), Op.ADDRESS())
        + Op.SSTORE(storage_pointer_code.store_next(3, "callvalue"), Op.CALLVALUE())
        + Op.CALL(gas=1000, address=0, value=3)
        + Op.SSTORE(storage_pointer_code.store_next(100, "selfbalance"), Op.SELFBALANCE())
        + Op.SSTORE(storage_pointer_code.store_next(sender, "origin"), Op.ORIGIN())
        + Op.SSTORE(
            storage_pointer_code.store_next(
                "0x1122334400000000000000000000000000000000000000000000000000000000",
                "calldataload",
            ),
            Op.CALLDATALOAD(0),
        )
        + Op.SSTORE(storage_pointer_code.store_next(4, "calldatasize"), Op.CALLDATASIZE())
        + Op.CALLDATACOPY(0, 0, 32)
        + Op.SSTORE(
            storage_pointer_code.store_next(
                "0x1122334400000000000000000000000000000000000000000000000000000000",
                "calldatacopy",
            ),
            Op.MLOAD(0),
        )
        + Op.MSTORE(0, 0)
        + Op.SSTORE(storage_pointer_code.store_next(83, "codesize"), Op.CODESIZE())
        + Op.CODECOPY(0, 0, 32)
        + Op.SSTORE(
            storage_pointer_code.store_next(
                "0x30600055346001556000600060006000600360006103e8f14760025532600355", "codecopy"
            ),
            Op.MLOAD(0),
        )
        + Op.SSTORE(storage_pointer_code.store_next(0, "sload"), Op.SLOAD(15)),
        storage={15: 25},
    )

    contract_measurements = pre.deploy_contract(
        code=Op.EXTCODECOPY(pointer, 0, 0, 32)
        + Op.SSTORE(
            storage_normal.store_next(Bytes().keccak256(), "extcodehash"),
            Op.EXTCODEHASH(pointer),
        )
        + Op.SSTORE(storage_normal.store_next(0, "extcodesize"), Op.EXTCODESIZE(pointer))
        + Op.SSTORE(storage_normal.store_next(0, "extcodecopy"), Op.MLOAD(0))
        + Op.SSTORE(storage_normal.store_next(100, "balance"), Op.BALANCE(pointer))
        + Op.STOP,
    )
    delegation_designation = Spec.delegation_designation(pointer_code)
    contract_measurements_pointer = pre.deploy_contract(
        code=Op.EXTCODECOPY(pointer, 0, 0, 32)
        + Op.SSTORE(
            storage_pointer.store_next(delegation_designation.keccak256(), "extcodehash"),
            Op.EXTCODEHASH(pointer),
        )
        + Op.SSTORE(
            storage_pointer.store_next(len(delegation_designation), "extcodesize"),
            Op.EXTCODESIZE(pointer),
        )
        + Op.SSTORE(
            storage_pointer.store_next(
                Hash(delegation_designation, right_padding=True), "extcodecopy"
            ),
            Op.MLOAD(0),
        )
        + Op.SSTORE(storage_pointer.store_next(100, "balance"), Op.BALANCE(pointer))
        + Op.STOP,
    )

    tx = Transaction(
        to=contract_measurements,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
    )

    tx_pointer = Transaction(
        to=contract_measurements_pointer,
        gas_limit=1_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=pointer_code,
                nonce=0,
                signer=pointer,
            )
        ],
    )

    tx_pointer_call = Transaction(
        to=pointer,
        gas_limit=1_000_000,
        data=bytes.fromhex("11223344"),
        value=3,
        sender=sender,
    )

    post = {
        contract_measurements: Account(storage=storage_normal),
        contract_measurements_pointer: Account(storage=storage_pointer),
        pointer: Account(storage=storage_pointer_code),
    }
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[Block(txs=[tx]), Block(txs=[tx_pointer, tx_pointer_call])],
    )


@pytest.mark.with_all_precompiles
@pytest.mark.valid_from("Prague")
def test_call_to_precompile_in_pointer_context(
    state_test: StateTestFiller, pre: Alloc, precompile: int
):
    """
    Tx -> call -> pointer A -> precompile contract
    Make sure that gas consumed when calling precompiles in normal call are the same
    As from inside the pointer context call.
    """
    env = Environment()

    storage: Storage = Storage()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_test = pre.deploy_contract(
        code=Op.MSTORE(1000, Op.GAS())
        + Op.CALL(gas=100_000, address=precompile, args_size=Op.CALLDATASIZE())
        + Op.MSTORE(0, Op.SUB(Op.MLOAD(1000), Op.GAS()))
        + Op.RETURN(0, 32)
    )
    normal_call_gas = 2000
    pointer_call_gas = 3000
    contract_a = pre.deploy_contract(
        code=Op.CALL(
            gas=1_000_000,
            address=contract_test,
            args_size=Op.CALLDATASIZE(),
            ret_offset=1000,
            ret_size=32,
        )
        + Op.MSTORE(normal_call_gas, Op.MLOAD(1000))
        + Op.CALL(
            gas=1_000_000,
            address=pointer_a,
            args_size=Op.CALLDATASIZE(),
            ret_offset=1000,
            ret_size=32,
        )
        + Op.MSTORE(pointer_call_gas, Op.MLOAD(1000))
        + Op.SSTORE(
            storage.store_next(0, "call_gas_diff"),
            Op.SUB(Op.MLOAD(normal_call_gas), Op.MLOAD(pointer_call_gas)),
        )
        + Op.SSTORE(storage.store_next(1, "tx_worked"), 1)
    )

    tx = Transaction(
        to=contract_a,
        gas_limit=3_000_000,
        data=[0x11] * 256,
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_test,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {contract_a: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.with_all_precompiles
@pytest.mark.valid_from("Prague")
def test_pointer_to_precompile(state_test: StateTestFiller, pre: Alloc, precompile: int):
    """
    Tx -> call -> pointer A -> precompile contract.

    In case a delegation designator points to a precompile address, retrieved code is considered
    empty and CALL, CALLCODE, STATICCALL, DELEGATECALL instructions targeting this account will
    execute empty code, i.e. succeed with no execution given enough gas.

    So call to a pointer that points to a precompile is like call to an empty account
    """
    env = Environment()

    storage: Storage = Storage()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_test_normal = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALL(gas=0, address=precompile, args_size=Op.CALLDATASIZE()))
        + Op.RETURN(0, 32)
    )

    contract_test_pointer = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALL(gas=0, address=pointer_a, args_size=Op.CALLDATASIZE()))
        + Op.RETURN(0, 32)
    )

    contract_a = pre.deploy_contract(
        code=Op.CALL(
            gas=1_000_000,
            address=contract_test_normal,
            args_size=Op.CALLDATASIZE(),
            ret_offset=1000,
            ret_size=32,
        )
        # direct call to a precompile with 0 gas always return 0
        + Op.SSTORE(storage.store_next(0, "direct_call_result"), Op.MLOAD(1000))
        + Op.CALL(
            gas=1_000_000,
            address=contract_test_pointer,
            args_size=Op.CALLDATASIZE(),
            ret_offset=1000,
            ret_size=32,
        )
        # pointer call to a precompile with 0 gas always return 1 as if calling empty address
        + Op.SSTORE(storage.store_next(1, "pointer_call_result"), Op.MLOAD(1000))
    )

    tx = Transaction(
        to=contract_a,
        gas_limit=3_000_000,
        data=[0x11] * 256,
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=precompile,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {contract_a: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


class AccessListCall(Enum):
    """Add addresses to access list."""

    NONE = 1
    IN_NORMAL_TX_ONLY = 2
    IN_POINTER_TX_ONLY = 3
    IN_BOTH_TX = 4


class PointerDefinition(Enum):
    """Define pointer in transactions."""

    SEPARATE = 1
    IN_NORMAL_TX_ONLY = 2
    IN_POINTER_TX_ONLY = 3
    IN_BOTH_TX = 4


class AccessListTo(Enum):
    """Define access list to."""

    POINTER_ADDRESS = 1
    CONTRACT_ADDRESS = 2


@pytest.mark.parametrize(
    "access_list_rule",
    [
        AccessListCall.NONE,
        AccessListCall.IN_BOTH_TX,
        AccessListCall.IN_NORMAL_TX_ONLY,
        AccessListCall.IN_POINTER_TX_ONLY,
    ],
)
@pytest.mark.parametrize(
    "pointer_definition",
    [
        PointerDefinition.SEPARATE,
        PointerDefinition.IN_BOTH_TX,
        PointerDefinition.IN_NORMAL_TX_ONLY,
        PointerDefinition.IN_POINTER_TX_ONLY,
    ],
)
@pytest.mark.parametrize(
    "access_list_to",
    [AccessListTo.POINTER_ADDRESS, AccessListTo.CONTRACT_ADDRESS],
)
@pytest.mark.valid_from("Prague")
def test_gas_diff_pointer_vs_direct_call(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    fork: Fork,
    access_list_rule: AccessListCall,
    pointer_definition: PointerDefinition,
    access_list_to: AccessListTo,
):
    """
    Check the gas difference when calling the contract directly vs as a pointer
    Combine with AccessList and AuthTuple gas reductions scenarios.
    """
    env = Environment()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    call_worked = 1
    gas_costs: GasCosts = fork.gas_costs()

    opcodes_price = 37
    direct_call_gas: int = (
        # 20_000 + 2_600 + 2_100 + 37 = 24737
        gas_costs.G_STORAGE_SET
        + (
            # access account price
            # If storage and account is declared in access list then discount
            gas_costs.G_WARM_ACCOUNT_ACCESS + gas_costs.G_WARM_SLOAD
            if access_list_rule in [AccessListCall.IN_NORMAL_TX_ONLY, AccessListCall.IN_BOTH_TX]
            else gas_costs.G_COLD_ACCOUNT_ACCESS + gas_costs.G_COLD_SLOAD
        )
        + opcodes_price
    )

    pointer_call_gas: int = (
        # sstore + addr + addr + sload + op
        # no access list, no pointer, all accesses are hot
        # 20_000 + 2_600 * 2 + 2_100 + 37 = 27_337
        #
        # access list for pointer, pointer is set
        # additional 2_600 charged for access of contract
        # 20_000 + 100 + 2_600 + 100 + 37 = 22_837
        #
        # no access list, pointer is set
        # pointer access is hot, sload and contract are hot
        # 20_000 + 100 + 2_600 + 2_100 + 37 = 24_837
        #
        # access list for contract, pointer is set
        # contract call is hot, pointer call is call because pointer is set
        # only sload is hot because access list is for contract
        # 20_000 + 100 + 100 + 2100  + 37 = 22_337
        gas_costs.G_STORAGE_SET
        # pointer address access
        + (
            gas_costs.G_WARM_ACCOUNT_ACCESS
            if (
                pointer_definition
                in [PointerDefinition.IN_BOTH_TX, PointerDefinition.IN_POINTER_TX_ONLY]
                or access_list_rule
                in [AccessListCall.IN_BOTH_TX, AccessListCall.IN_POINTER_TX_ONLY]
                and access_list_to == AccessListTo.POINTER_ADDRESS
            )
            else gas_costs.G_COLD_ACCOUNT_ACCESS
        )
        # storage access
        + (
            gas_costs.G_WARM_SLOAD
            if (
                access_list_rule in [AccessListCall.IN_BOTH_TX, AccessListCall.IN_POINTER_TX_ONLY]
                and access_list_to == AccessListTo.POINTER_ADDRESS
            )
            else gas_costs.G_COLD_SLOAD
        )
        # contract address access
        + (
            gas_costs.G_WARM_ACCOUNT_ACCESS
            if (
                access_list_rule in [AccessListCall.IN_BOTH_TX, AccessListCall.IN_POINTER_TX_ONLY]
                and access_list_to == AccessListTo.CONTRACT_ADDRESS
            )
            else gas_costs.G_COLD_ACCOUNT_ACCESS
        )
        + opcodes_price
    )

    contract = pre.deploy_contract(code=Op.SSTORE(call_worked, Op.ADD(Op.SLOAD(call_worked), 1)))

    # Op.CALLDATASIZE() does not work with kwargs
    storage_normal: Storage = Storage()
    contract_test_normal = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=100_000, address=contract))
        + Op.SSTORE(
            storage_normal.store_next(direct_call_gas, "normal_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    storage_pointer: Storage = Storage()
    contract_test_pointer = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=100_000, address=pointer_a))
        + Op.SSTORE(
            storage_pointer.store_next(pointer_call_gas, "pointer_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    tx_0 = Transaction(
        to=1,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=(
            [
                AuthorizationTuple(
                    address=contract,
                    nonce=0,
                    signer=pointer_a,
                )
            ]
            if pointer_definition == PointerDefinition.SEPARATE
            else None
        ),
    )

    tx = Transaction(
        to=contract_test_normal,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=(
            [
                AuthorizationTuple(
                    address=contract,
                    nonce=0,
                    signer=pointer_a,
                )
            ]
            if pointer_definition == PointerDefinition.IN_BOTH_TX
            or pointer_definition == PointerDefinition.IN_NORMAL_TX_ONLY
            else None
        ),
        access_list=(
            [
                AccessList(
                    address=contract,
                    storage_keys=[call_worked],
                )
            ]
            if access_list_rule == AccessListCall.IN_BOTH_TX
            or access_list_rule == AccessListCall.IN_NORMAL_TX_ONLY
            else None
        ),
    )
    tx2 = Transaction(
        to=contract_test_pointer,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=(
            [
                AuthorizationTuple(
                    address=contract,
                    nonce=0,
                    signer=pointer_a,
                )
            ]
            if pointer_definition == PointerDefinition.IN_BOTH_TX
            or pointer_definition == PointerDefinition.IN_POINTER_TX_ONLY
            else None
        ),
        access_list=(
            [
                AccessList(
                    address=(
                        pointer_a if access_list_to == AccessListTo.POINTER_ADDRESS else contract
                    ),
                    storage_keys=[call_worked],
                )
            ]
            if access_list_rule == AccessListCall.IN_BOTH_TX
            or access_list_rule == AccessListCall.IN_POINTER_TX_ONLY
            else None
        ),
    )

    post = {
        contract: Account(storage={call_worked: 1}),
        pointer_a: Account(storage={call_worked: 1}),
        contract_test_normal: Account(storage=storage_normal),
        contract_test_pointer: Account(storage=storage_pointer),
    }
    blockchain_test(
        genesis_environment=env,
        pre=pre,
        post=post,
        blocks=[Block(txs=[tx_0]), Block(txs=[tx]), Block(txs=[tx2])],
    )


@pytest.mark.valid_from("Prague")
def test_pointer_call_followed_by_direct_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
):
    """
    If we first call by pointer then direct call, will the call/sload be hot
    The direct call will warm because pointer access marks it warm
    But the sload is still cold because
    storage marked hot from pointer's account in a pointer call.
    """
    env = Environment()

    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()
    gas_costs: GasCosts = fork.gas_costs()
    call_worked = 1
    opcodes_price: int = 37
    pointer_call_gas = (
        gas_costs.G_STORAGE_SET
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # pointer is warm
        + gas_costs.G_COLD_ACCOUNT_ACCESS  # contract is cold
        + gas_costs.G_COLD_SLOAD  # storage access under pointer call is cold
        + opcodes_price
    )
    direct_call_gas = (
        gas_costs.G_STORAGE_SET
        + gas_costs.G_WARM_ACCOUNT_ACCESS  # since previous pointer call, contract is now warm
        + gas_costs.G_COLD_SLOAD  # but storage is cold, because it's contract's direct
        + opcodes_price
    )

    contract = pre.deploy_contract(code=Op.SSTORE(call_worked, Op.ADD(Op.SLOAD(call_worked), 1)))

    storage_test_gas: Storage = Storage()
    contract_test_gas = pre.deploy_contract(
        code=Op.GAS()
        + Op.POP(Op.CALL(gas=100_000, address=pointer_a))
        + Op.SSTORE(
            storage_test_gas.store_next(pointer_call_gas, "pointer_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
        + Op.GAS()
        + Op.POP(Op.CALL(gas=100_000, address=contract))
        + Op.SSTORE(
            storage_test_gas.store_next(direct_call_gas, "direct_call_price"),
            Op.SUB(Op.SWAP1(), Op.GAS()),
        )
    )

    tx = Transaction(
        to=contract_test_gas,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=(
            [
                AuthorizationTuple(
                    address=contract,
                    nonce=0,
                    signer=pointer_a,
                )
            ]
        ),
    )

    post = {
        contract: Account(storage={call_worked: 1}),
        pointer_a: Account(storage={call_worked: 1}),
        contract_test_gas: Account(storage=storage_test_gas),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_pointer_to_static(state_test: StateTestFiller, pre: Alloc):
    """
    Tx -> call -> pointer A -> static -> static violation
    Verify that static context is active when called under pointer.
    """
    env = Environment()
    storage: Storage = Storage()
    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_b = pre.deploy_contract(code=Op.SSTORE(0, 5))
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(0, "static_call"),
            Op.STATICCALL(
                gas=1_000_000, address=contract_b, args_size=32, ret_offset=1000, ret_size=32
            ),
        )
        + Op.SSTORE(storage.store_next(1, "call_worked"), 1)
    )

    tx = Transaction(
        to=pointer_a,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {pointer_a: Account(storage=storage), contract_b: Account(storage={0: 0})}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_static_to_pointer(state_test: StateTestFiller, pre: Alloc):
    """
    Tx -> staticcall -> pointer A -> static violation
    Verify that static context is active when make sub call to pointer.
    """
    env = Environment()
    storage: Storage = Storage()
    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_b = pre.deploy_contract(code=Op.SSTORE(0, 5))
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(0, "static_call"),
            Op.STATICCALL(
                gas=1_000_000, address=pointer_a, args_size=32, ret_offset=1000, ret_size=32
            ),
        )
        + Op.SSTORE(storage.store_next(1, "call_worked"), 1)
    )

    tx = Transaction(
        to=contract_a,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_b,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {contract_a: Account(storage=storage), pointer_a: Account(storage={0: 0})}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Osaka")
def test_pointer_to_eof(state_test: StateTestFiller, pre: Alloc):
    """
    Tx -> call -> pointer A -> EOF
    Pointer to eof contract works.
    """
    env = Environment()
    storage: Storage = Storage()
    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_a = pre.deploy_contract(
        code=Container(
            sections=[
                Section.Code(
                    code=Op.SSTORE(storage.store_next(5, "eof_call_result"), 5) + Op.STOP,
                )
            ]
        )
    )

    tx = Transaction(
        to=pointer_a,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {pointer_a: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_pointer_to_static_reentry(state_test: StateTestFiller, pre: Alloc):
    """
    Tx call -> pointer A -> static -> code -> pointer A -> static violation
    Verify that static context is active when called under pointer.
    """
    env = Environment()
    storage: Storage = Storage()
    sender = pre.fund_eoa()
    pointer_a = pre.fund_eoa()

    contract_b = pre.deploy_contract(
        code=Op.MSTORE(0, Op.ADD(1, Op.CALLDATALOAD(0)))
        + Conditional(
            condition=Op.EQ(Op.MLOAD(0), 2), if_true=Op.SSTORE(5, 5), if_false=Op.JUMPDEST()
        )
        + Op.CALL(gas=100_000, address=pointer_a, args_offset=0, args_size=Op.CALLDATASIZE())
    )
    contract_a = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Conditional(
            condition=Op.EQ(Op.MLOAD(0), 0),
            if_true=Op.SSTORE(
                storage.store_next(1, "static_call"),
                Op.STATICCALL(
                    gas=1_000_000,
                    address=contract_b,
                    args_size=Op.CALLDATASIZE(),
                    ret_offset=1000,
                    ret_size=32,
                ),
            )
            + Op.SSTORE(storage.store_next(1, "call_worked"), 1),
            if_false=Op.CALL(
                gas=1_000_000,
                address=contract_b,
                args_size=Op.CALLDATASIZE(),
                ret_offset=1000,
                ret_size=32,
            ),
        )
    )

    tx = Transaction(
        to=pointer_a,
        gas_limit=3_000_000,
        data=[0x00] * 32,
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_a,
                nonce=0,
                signer=pointer_a,
            )
        ],
    )

    post = {pointer_a: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "call_type",
    [Op.CALL, Op.DELEGATECALL, Op.CALLCODE],
)
def test_contract_storage_to_pointer_with_storage(
    state_test: StateTestFiller, pre: Alloc, call_type: Op
):
    """
    Tx call -> contract with storage -> pointer A with storage -> storage/tstorage modify
    Check storage/tstorage modifications when interacting with pointers.
    """
    env = Environment()

    sender = pre.fund_eoa()

    # Pointer B
    storage_pointer_b: Storage = Storage()
    storage_pointer_b.store_next(
        0 if call_type in [Op.DELEGATECALL, Op.CALLCODE] else 1, "first_slot"
    )
    storage_pointer_b.store_next(0, "second_slot")
    storage_pointer_b.store_next(0, "third_slot")
    pointer_b = pre.fund_eoa()

    # Contract B
    storage_b: Storage = Storage()
    first_slot = storage_b.store_next(10, "first_slot")
    second_slot = storage_b.store_next(20, "second_slot")
    third_slot = storage_b.store_next(30, "third_slot")
    fourth_slot = storage_b.store_next(0, "fourth_slot")
    contract_b = pre.deploy_contract(
        code=Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=Op.SSTORE(fourth_slot, Op.TLOAD(third_slot)),
            if_false=Op.SSTORE(first_slot, Op.ADD(Op.SLOAD(first_slot), 1))
            + Op.TSTORE(third_slot, Op.ADD(Op.TLOAD(third_slot), 1)),
        ),
        storage={
            # Original contract storage is untouched
            first_slot: 10,
            second_slot: 20,
            third_slot: 30,
        },
    )

    # Contract A
    storage_a: Storage = Storage()
    contract_a = pre.deploy_contract(
        code=Op.TSTORE(third_slot, 1)
        + call_type(address=pointer_b, gas=500_000)
        + Op.SSTORE(third_slot, Op.TLOAD(third_slot))
        # Verify tstorage in contract after interacting with pointer, it must be 0
        + Op.MSTORE(0, 1)
        + Op.CALL(address=contract_b, gas=500_000, args_offset=0, args_size=32),
        storage={
            storage_a.store_next(
                # caller storage is modified when calling pointer with delegate or callcode
                6 if call_type in [Op.DELEGATECALL, Op.CALLCODE] else 5,
                "first_slot",
            ): 5,
            storage_a.store_next(2, "second_slot"): 2,
            storage_a.store_next(
                # TSTORE is modified when calling pointer with delegate or callcode
                2 if call_type in [Op.DELEGATECALL, Op.CALLCODE] else 1,
                "third_slot",
            ): 3,
        },
    )

    tx = Transaction(
        to=contract_a,
        gas_limit=3_000_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_b,
                nonce=0,
                signer=pointer_b,
            )
        ],
    )

    post = {
        contract_a: Account(storage=storage_a),
        contract_b: Account(storage=storage_b),
        pointer_b: Account(storage=storage_pointer_b),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


class ReentryAction(IntEnum):
    """Reentry logic action."""

    CALL_PROXY = 0
    MEASURE_VALUES = 1
    MEASURE_VALUES_CONTRACT = 2


@pytest.mark.valid_from("Prague")
def test_pointer_reentry(state_test: StateTestFiller, pre: Alloc):
    """
    Check operations when reenter the pointer again
    TODO: feel free to extend the code checks under given scenarios in switch case.
    """
    env = Environment()
    arg_contract = 0
    arg_action = 32

    storage_b = Storage()
    storage_b.store_next(1, "contract_calls")
    storage_b.store_next(1, "tstore_slot")
    slot_reentry_address = storage_b.store_next(1, "address")

    storage_pointer_b = Storage()
    slot_calls = storage_pointer_b.store_next(2, "pointer_calls")
    slot_tstore = storage_pointer_b.store_next(2, "tstore_slot")

    sender = pre.fund_eoa()
    pointer_b = pre.fund_eoa(amount=1000)
    proxy = pre.deploy_contract(
        code=Op.MSTORE(arg_contract, Op.CALLDATALOAD(arg_contract))
        + Op.MSTORE(arg_action, Op.CALLDATALOAD(arg_action))
        + Op.CALL(gas=400_000, address=pointer_b, args_offset=0, args_size=32 * 2)
    )
    contract_b = pre.deploy_contract(
        balance=100,
        code=Op.MSTORE(arg_contract, Op.CALLDATALOAD(arg_contract))
        + Op.MSTORE(arg_action, Op.CALLDATALOAD(arg_action))
        + Op.SSTORE(slot_calls, Op.ADD(Op.SLOAD(slot_calls), 1))
        + Op.TSTORE(slot_tstore, Op.ADD(Op.TLOAD(slot_tstore), 1))
        + Op.SSTORE(slot_tstore, Op.TLOAD(slot_tstore))
        + Switch(
            cases=[
                Case(
                    condition=Op.EQ(Op.MLOAD(arg_action), ReentryAction.CALL_PROXY),
                    action=Op.MSTORE(arg_action, ReentryAction.MEASURE_VALUES)
                    + Op.CALL(gas=500_000, address=proxy, args_offset=0, args_size=32 * 2)
                    + Op.STOP(),
                ),
                Case(
                    # This code is executed under pointer -> proxy -> pointer context
                    condition=Op.EQ(Op.MLOAD(arg_action), ReentryAction.MEASURE_VALUES),
                    action=Op.SSTORE(storage_pointer_b.store_next(sender, "origin"), Op.ORIGIN())
                    + Op.SSTORE(storage_pointer_b.store_next(pointer_b, "address"), Op.ADDRESS())
                    + Op.SSTORE(
                        storage_pointer_b.store_next(1000, "selfbalance"), Op.SELFBALANCE()
                    )
                    + Op.SSTORE(storage_pointer_b.store_next(proxy, "caller"), Op.CALLER())
                    # now call contract which is pointer dest directly
                    + Op.MSTORE(arg_action, ReentryAction.MEASURE_VALUES_CONTRACT)
                    + Op.CALL(
                        gas=500_000,
                        address=Op.MLOAD(arg_contract),
                        args_offset=0,
                        args_size=32 * 2,
                    ),
                ),
                Case(
                    # This code is executed under
                    # pointer -> proxy -> pointer -> contract
                    # so pointer calling the code of it's dest after reentry to itself
                    condition=Op.EQ(Op.MLOAD(arg_action), ReentryAction.MEASURE_VALUES_CONTRACT),
                    action=Op.SSTORE(storage_b.store_next(sender, "origin"), Op.ORIGIN())
                    + Op.SSTORE(slot_reentry_address, Op.ADDRESS())
                    + Op.SSTORE(storage_b.store_next(100, "selfbalance"), Op.SELFBALANCE())
                    + Op.SSTORE(storage_b.store_next(pointer_b, "caller"), Op.CALLER()),
                ),
            ],
            default_action=None,
        ),
    )

    storage_b[slot_reentry_address] = contract_b

    tx = Transaction(
        to=pointer_b,
        gas_limit=2_000_000,
        data=Hash(contract_b, left_padding=True)
        + Hash(ReentryAction.CALL_PROXY, left_padding=True),
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_b,
                nonce=0,
                signer=pointer_b,
            )
        ],
    )
    post = {
        contract_b: Account(storage=storage_b),
        pointer_b: Account(storage=storage_pointer_b),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_eoa_init_as_pointer(state_test: StateTestFiller, pre: Alloc):
    """
    It was agreed before that senders don't have code
    And there were issues with tests sending transactions from account's with code
    With EIP7702 it is again possible, let's check the test runners are ok.
    """
    env = Environment()
    storage = Storage()
    contract = pre.deploy_contract(code=Op.SSTORE(storage.store_next(1, "code_worked"), 1))
    sender = pre.fund_eoa(delegation=contract)

    tx = Transaction(
        to=sender,
        gas_limit=200_000,
        data=b"",
        value=0,
        sender=sender,
    )
    post = {sender: Account(storage=storage)}
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("call_return", [Op.RETURN, Op.REVERT, Macros.OOG])
def test_call_pointer_to_created_from_create_after_oog_call_again(
    state_test: StateTestFiller, pre: Alloc, call_return: Op
):
    """
    Set pointer to account that we are about to create.

    Pointer is set to create address that is yet not in the state
    During the call, address is created. pointer is called from init code to do nothing
    Then after account is created it is called again to run created code

    Then revert / no revert

    Call pointer again from the upper level to ensure it does not call reverted code
    """
    env = Environment()

    storage_pointer = Storage()
    pointer = pre.fund_eoa()
    sender = pre.fund_eoa()

    storage_contract = Storage()
    slot_create_res = storage_contract.store_next(1, "create_result")
    contract = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.MSTORE(32, Op.CALLDATALOAD(32))
        + Op.SSTORE(slot_create_res, Op.CREATE(0, 0, Op.CALLDATASIZE()))
        + Op.CALL(address=pointer)
        + call_return(0, 32)
    )
    contract_main = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.MSTORE(32, Op.CALLDATALOAD(32))
        + Op.CALL(address=contract, args_size=Op.CALLDATASIZE())
        + Op.CALL(address=pointer)
    )
    contract_create = compute_create_address(address=contract, nonce=1)
    storage_contract[slot_create_res] = contract_create if call_return == Op.RETURN else 0

    slot_pointer_calls = storage_pointer.store_next(
        1 + 1 if call_return == Op.RETURN else 0, "pointer_calls"
    )
    deploy_code = Op.SSTORE(
        slot_pointer_calls,
        Op.ADD(1, Op.SLOAD(slot_pointer_calls)),
    )
    storage_create = Storage()
    tx = Transaction(
        to=contract_main,
        gas_limit=800_000,
        data=Op.SSTORE(storage_create.store_next(1, "create_init_code"), 1)
        + Op.SSTORE(
            storage_create.store_next(1, "call_pointer_from_init"), Op.CALL(address=pointer)
        )
        + Op.MSTORE(0, deploy_code.hex())
        + Op.RETURN(32 - len(deploy_code), len(deploy_code)),
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_create,
                nonce=0,
                signer=pointer,
            )
        ],
    )
    post = {
        contract_create: Account(storage=storage_create) if call_return == Op.RETURN else None,
        contract: Account(storage=storage_contract),
        pointer: Account(storage=storage_pointer),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


# Pointer Revert Contract Revert
# pointer set its storage, contract set its storage
# pointer set its storage, (contract set its storage, revert)
# (pointer set its storage, revert), contract set its storage
# (pointer set its storage, revert), (contract set its storage revert)
# contract set its storage, pointer set its storage
# contract set its storage, (pointer set its storage, revert)
# (contract set its storage, revert), pointer set its storage
# (contract set its storage, revert), (pointer set its storage revert)
# (pointer set its storage, contract set its storage), revert
# (contract set its storage, pointer set its storage), revert
class CallOrder(Enum):
    """Add addresses to access list."""

    POINTER_CONTRACT = 1
    CONTRACT_POINTER = 2


valid_combinations = [
    (True, True, False),
    (True, False, False),
    (False, True, False),
    (False, False, False),
    (False, False, True),
]


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize("first_revert, second_revert, final_revert", valid_combinations)
@pytest.mark.parametrize("call_order", [CallOrder.CONTRACT_POINTER, CallOrder.POINTER_CONTRACT])
def test_pointer_reverts(
    state_test: StateTestFiller,
    pre: Alloc,
    first_revert: bool,
    second_revert: bool,
    final_revert: bool,
    call_order: CallOrder,
):
    """Pointer do operations then revert."""
    sender = pre.fund_eoa()
    pointer = pre.fund_eoa()

    contract_storage = Storage()
    contract_calls = (
        0
        if (call_order == CallOrder.CONTRACT_POINTER and first_revert)
        or (call_order == CallOrder.POINTER_CONTRACT and second_revert)
        or final_revert
        else 1
    )
    slot_storage = contract_storage.store_next(contract_calls, "storage")
    slot_tstorage = contract_storage.store_next(contract_calls, "tstorage")

    pointer_storage = Storage()
    pointer_calls = (
        0
        if (call_order == CallOrder.POINTER_CONTRACT and first_revert)
        or (call_order == CallOrder.CONTRACT_POINTER and second_revert)
        or final_revert
        else 1
    )
    pointer_storage.store_next(pointer_calls, "storage")
    pointer_storage.store_next(pointer_calls, "tstorage")

    contract = pre.deploy_contract(
        code=Op.SSTORE(slot_storage, Op.ADD(1, Op.SLOAD(slot_storage)))
        + Op.TSTORE(0, Op.ADD(1, Op.TLOAD(0)))
        + Op.SSTORE(slot_tstorage, Op.TLOAD(0))
        + Conditional(
            condition=Op.EQ(Op.CALLDATALOAD(0), 1),
            if_true=Op.REVERT(0, 32),
            if_false=Op.RETURN(0, 32),
        )
    )
    contract_main = pre.deploy_contract(
        code=Op.MSTORE(0, 1 if first_revert else 0)
        + Op.CALL(
            address=pointer if call_order == CallOrder.POINTER_CONTRACT else contract, args_size=32
        )
        + Op.MSTORE(0, 1 if second_revert else 0)
        + Op.CALL(
            address=pointer if call_order == CallOrder.CONTRACT_POINTER else contract, args_size=32
        )
        + Conditional(
            condition=Op.EQ(1, int(final_revert)),
            if_true=Op.REVERT(0, 32),
            if_false=Op.RETURN(0, 32),
        )
    )
    tx = Transaction(
        to=contract_main,
        gas_limit=800_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract,
                nonce=0,
                signer=pointer,
            )
        ],
    )
    post = {pointer: Account(storage=pointer_storage), contract: Account(storage=contract_storage)}
    state_test(
        env=Environment(),
        pre=pre,
        post=post,
        tx=tx,
    )


class DelegationTo(Enum):
    """Add addresses to access list."""

    CONTRACT_A = 1
    CONTRACT_B = 2
    RESET = 3


@pytest.mark.valid_from("Prague")
@pytest.mark.parametrize(
    "first_delegation", [DelegationTo.CONTRACT_A, DelegationTo.CONTRACT_B, DelegationTo.RESET]
)
@pytest.mark.parametrize(
    "second_delegation", [DelegationTo.CONTRACT_A, DelegationTo.CONTRACT_B, DelegationTo.RESET]
)
def test_double_auth(
    state_test: StateTestFiller,
    pre: Alloc,
    first_delegation: DelegationTo,
    second_delegation: DelegationTo,
):
    """Only the last auth works, but first auth still charges the gas."""
    env = Environment()
    sender = pre.fund_eoa()
    pointer = pre.fund_eoa()

    storage = Storage()
    contract_a = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(
                1 if second_delegation == DelegationTo.CONTRACT_A else 0, "code_a_worked"
            ),
            1,
        )
    )
    contract_b = pre.deploy_contract(
        code=Op.SSTORE(
            storage.store_next(
                2 if second_delegation == DelegationTo.CONTRACT_B else 0, "code_b_worked"
            ),
            2,
        )
    )

    main_storage = Storage()
    contract_main = pre.deploy_contract(code=Op.CALL(address=pointer))

    tx = Transaction(
        to=contract_main,
        gas_limit=200_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=(
                    contract_a
                    if first_delegation == DelegationTo.CONTRACT_A
                    else contract_b
                    if first_delegation == DelegationTo.CONTRACT_B
                    else 0
                ),
                nonce=0,
                signer=pointer,
            ),
            AuthorizationTuple(
                address=(
                    contract_a
                    if second_delegation == DelegationTo.CONTRACT_A
                    else contract_b
                    if second_delegation == DelegationTo.CONTRACT_B
                    else 0
                ),
                nonce=1,
                signer=pointer,
            ),
        ],
    )
    post = {
        pointer: (
            Account(
                storage=storage,
                code=(
                    Spec.delegation_designation(contract_a)
                    if second_delegation == DelegationTo.CONTRACT_A
                    else (
                        Spec.delegation_designation(contract_b)
                        if second_delegation == DelegationTo.CONTRACT_B
                        else bytes()
                    )
                ),
            )
        ),
        contract_main: Account(storage=main_storage),
    }
    state_test(
        env=env,
        pre=pre,
        post=post,
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_pointer_resets_an_empty_code_account_with_storage(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
):
    """
    So in Block1 we create a sender with empty code, but non empty storage using pointers
    In Block2 we create account that perform suicide, then we check that when calling
    a pointer, that points to newly created account and runs suicide,
    is not deleted as well as its storage.

    This one is a little messy.
    """
    sender = pre.fund_eoa()
    pointer = pre.fund_eoa(amount=0)
    pointer_storage = Storage()
    sender_storage = Storage()
    sender_storage.store_next(1, "slot1")
    sender_storage.store_next(2, "slot2")
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(pointer_storage.store_next(1, "slot1"), 1)
        + Op.SSTORE(pointer_storage.store_next(2, "slot2"), 2)
    )

    tx_set_pointer_storage = Transaction(
        to=pointer,
        gas_limit=200_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_1,
                nonce=0,
                signer=pointer,
            ),
        ],
    )
    tx_set_sender_storage = Transaction(
        to=sender,
        gas_limit=200_000,
        data=b"",
        value=0,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=contract_1,
                nonce=2,
                signer=sender,
            ),
        ],
    )

    tx_reset_code = Transaction(
        to=pointer,
        gas_limit=200_000,
        data=b"",
        value=0,
        nonce=3,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=0,
                nonce=1,
                signer=pointer,
            ),
            AuthorizationTuple(
                address=0,
                nonce=4,
                signer=sender,
            ),
        ],
    )

    contract_2 = pre.deploy_contract(code=Op.SSTORE(1, 1))
    tx_send_from_empty_code_with_storage = Transaction(
        to=contract_2,
        gas_limit=200_000,
        data=b"",
        value=0,
        nonce=5,
        sender=sender,
    )

    # Block 2
    # Sender with storage and pointer code calling selfdestruct on itself
    # But it points to a newly created account, check that pointer storage is not deleted
    suicide_dest = pre.fund_eoa(amount=0)
    deploy_code = Op.SSTORE(5, 5) + Op.SELFDESTRUCT(suicide_dest)
    sender_storage[5] = 5

    another_pointer = pre.fund_eoa()

    contract_create = pre.deploy_contract(
        code=Op.MSTORE(0, Op.CALLDATALOAD(0))
        + Op.MSTORE(32, Op.CALLDATALOAD(32))
        + Op.SSTORE(1, Op.CREATE(0, 0, Op.CALLDATASIZE()))
        + Op.CALL(address=sender)  # run suicide from pointer
        + Op.CALL(address=Op.SLOAD(1))  # run suicide directly
        + Op.CALL(address=another_pointer)  # run suicide from pointer that is not sender
    )
    newly_created_address = compute_create_address(address=contract_create, nonce=1)

    tx_create_suicide_from_pointer = Transaction(
        to=contract_create,
        gas_limit=800_000,
        data=Op.SSTORE(6, 6)
        + Op.MSTORE(0, deploy_code.hex())
        + Op.RETURN(32 - len(deploy_code), len(deploy_code)),
        value=1000,
        nonce=6,
        sender=sender,
        authorization_list=[
            AuthorizationTuple(
                address=newly_created_address,
                nonce=7,
                signer=sender,
            ),
            AuthorizationTuple(
                address=newly_created_address,
                nonce=0,
                signer=another_pointer,
            ),
        ],
    )

    post = {
        pointer: Account(nonce=2, balance=0, storage=pointer_storage, code=bytes()),
        sender: Account(
            storage=sender_storage, code=Spec.delegation_designation(newly_created_address)
        ),
        newly_created_address: Account.NONEXISTENT,
        contract_create: Account(storage={1: newly_created_address}),
        another_pointer: Account(balance=0, storage={5: 5}),
    }
    blockchain_test(
        genesis_environment=Environment(),
        pre=pre,
        post=post,
        blocks=[
            # post = {
            #    pointer: Account(nonce=2, balance=0, storage=pointer_storage, code=bytes()),
            #    sender: Account(storage=pointer_storage, code=bytes()),
            # }
            Block(
                txs=[
                    tx_set_pointer_storage,
                    tx_set_sender_storage,
                    tx_reset_code,
                    tx_send_from_empty_code_with_storage,
                ]
            ),
            Block(txs=[tx_create_suicide_from_pointer]),
        ],
    )
