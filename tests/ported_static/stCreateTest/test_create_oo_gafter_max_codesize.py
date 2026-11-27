"""
Create max code size contracts, revert some via OOG, self-destruct others.

Ported from:
state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytecode,
    Conditional,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_GAS_LIMIT = 0x100000000
RETURN_OFFSET = 0x40


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
# The transaction needs ~4.3e9 gas, over the Osaka transaction gas cap.
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize(
    "contract_count, delegate_create, subcall_oog",
    [
        pytest.param(
            10,
            False,
            True,
            id="LowContractCount_NoDelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            10,
            True,
            True,
            id="LowContractCount_DelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            10,
            True,
            False,
            id="LowContractCount_DelegateCreate_CallCreate_SelfDestruct",
        ),
        pytest.param(
            250,
            False,
            True,
            id="HighContractCount_NoDelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            250,
            True,
            True,
            id="HighContractCount_DelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            250,
            True,
            False,
            id="HighContractCount_DelegateCreate_CallCreate_SelfDestruct",
        ),
    ],
)
def test_create_oo_gafter_max_codesize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    contract_count: int,
    delegate_create: bool,
    subcall_oog: bool,
) -> None:
    """Create max code size contracts, revert some, self-destruct others."""
    sender = pre.fund_eoa()
    max_code_size = fork.max_code_size()

    # Source: yul
    # berlin
    # {
    #   // If calldata > 0, self-destruct, otherwise
    #   sstore(0, codesize())
    #   if gt(calldatasize(), 0) {
    #     selfdestruct(0)
    #   }
    # }
    created_code = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CODESIZE)
        + Conditional(
            condition=Op.GT(Op.CALLDATASIZE, 0),
            if_true=Op.SELFDESTRUCT(address=0x0),
        )
        + Op.STOP,
    )
    initcode_source = pre.deploy_contract(
        code=Op.EXTCODECOPY(
            address=created_code,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(created_code),
        )
        + Op.RETURN(offset=0x0, size=max_code_size),
    )
    initcode_size = Op.EXTCODESIZE(initcode_source)

    # Create as many max code size contracts as the second calldata word
    # (up to `contract_count`) and return their addresses, or halt if the
    # first calldata word is non-zero.
    creator_code = Op.SSTORE(key=1, value=1) + Op.EXTCODECOPY(
        address=initcode_source, dest_offset=0, offset=0, size=initcode_size
    )
    created_list_offset = 0x100
    for i in range(contract_count):
        creator_code += Conditional(
            condition=Op.GT(Op.CALLDATALOAD(offset=0x20), i),
            if_true=Op.MSTORE(
                offset=created_list_offset + i * 32,
                value=Op.CREATE(value=0, offset=0, size=initcode_size),
            ),
        )
    creator_code += Conditional(
        condition=Op.CALLDATALOAD(offset=0), if_true=Op.INVALID
    ) + Op.RETURN(offset=created_list_offset, size=contract_count * 32)
    creator = pre.deploy_contract(code=creator_code)

    delegate_count = contract_count if delegate_create else 0
    subcall_offset = RETURN_OFFSET + delegate_count * 32
    code = Bytecode()
    code += (
        Op.MSTORE(offset=0, value=0)
        + Op.MSTORE(offset=0x20, value=delegate_count)
        + Conditional(
            condition=Op.ISZERO(
                Op.DELEGATECALL(
                    gas=Op.DIV(Op.GAS, 2),
                    address=creator,
                    args_offset=0,
                    args_size=0x40,
                    ret_offset=RETURN_OFFSET,
                    ret_size=delegate_count * 32,
                )
            ),
            if_true=Op.REVERT(offset=0, size=0),
        )
    )
    subcall = Op.CALL(
        gas=Op.DIV(Op.GAS, 2),
        address=creator,
        args_offset=0,
        args_size=0x40,
        ret_offset=subcall_offset,
        ret_size=contract_count * 32,
    )
    code += Op.MSTORE(offset=0, value=int(subcall_oog)) + Op.MSTORE(
        offset=0x20, value=contract_count
    )
    if subcall_oog:
        code += Op.POP(subcall)
        created_count = delegate_count
        selfdestruct_count = 0
    else:
        code += Conditional(
            condition=Op.ISZERO(subcall),
            if_true=Op.REVERT(offset=0, size=0),
        )
        created_count = delegate_count + contract_count
        selfdestruct_count = created_count - 6
    for i in range(created_count):
        code += Op.POP(
            Op.CALL(
                gas=Op.SUB(Op.GAS, 1000),
                address=Op.MLOAD(offset=RETURN_OFFSET + i * 32),
            )
        )
    for i in range(selfdestruct_count):
        code += Op.POP(
            Op.CALL(
                gas=Op.SUB(Op.GAS, 1000),
                address=Op.MLOAD(offset=RETURN_OFFSET + i * 32),
                args_size=1,
            )
        )
    test_contract = pre.deploy_contract(code=code + Op.STOP)

    created_by_test = [
        compute_create_address(address=test_contract, nonce=1 + i)
        for i in range(delegate_count)
    ]
    created_by_creator = [
        compute_create_address(address=creator, nonce=1 + i)
        for i in range(contract_count)
    ]
    post: dict = {
        test_contract: Account(storage={1: 1}, nonce=1 + delegate_count),
    }
    if subcall_oog:
        post[creator] = Account(storage={}, nonce=1)
    else:
        post[creator] = Account(storage={1: 1}, nonce=1 + contract_count)
    for i, address in enumerate(created_by_test + created_by_creator):
        if i < selfdestruct_count or (subcall_oog and i >= delegate_count):
            post[address] = Account.NONEXISTENT
        else:
            post[address] = Account(storage={0: max_code_size})

    tx = Transaction(sender=sender, to=test_contract, gas_limit=TX_GAS_LIMIT)

    state_test(
        env=Environment(gas_limit=TX_GAS_LIMIT), pre=pre, post=post, tx=tx
    )
