"""
Verify recursively self-creating Solidity contracts stop when the
transaction budget runs dry, leaving exactly one child.

Ported from:
state_tests/stSolidityTest/RecursiveCreateContractsFiller.json

@manually-enhanced: Do not overwrite. The EIP-8037 state gas of the
in-test creations is added to the ported budget as a fork-derived
surcharge (exactly 0 before EIP-8037), preserving the ported
behavior on every fork.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSolidityTest/RecursiveCreateContractsFiller.json"],
)
@pytest.mark.valid_from("SpuriousDragon")
def test_recursive_create_contracts(
    state_test: StateTestFiller, pre: Alloc, fork: Fork
) -> None:
    """Recursive contract creation runs dry at the expected depth."""
    sender = pre.fund_eoa()

    # Source: solidity
    # contract recursiveCreate1
    # {
    #     uint depp;
    #     function recursiveCreate1(address a, uint depth)
    #     {
    #         depth = depth - 1;
    #         depp = depth;
    #         if (depth > 0)
    #             main(a).create2(depth);          // CALL back into main
    #     }
    # }
    #

    constructor_args_size = 0x40  # (address a, uint depth)

    return_contract_code = Op.JUMPDEST + Op.MSTORE(0, 0) + Op.RETURN(0, 1)
    args_memory_offset = 0x40
    depth = Op.SUB(Op.MLOAD(offset=args_memory_offset + 0x20), 1)
    initcode_1_p1 = (
        Op.CODECOPY(
            dest_offset=args_memory_offset,
            offset=Op.PUSH1(data_placeholder="initcode_size"),
            size=constructor_args_size,
        )
        + Op.SSTORE(0, depth)
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="callback_jumpdest"),
            condition=Op.GT(depth, 0),
        )
        + return_contract_code
    )
    initcode_1_p2 = (
        Op.JUMPDEST  # Callback jumpdest
        + Op.MSTORE(
            offset=0,
            value=depth,
        )
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="return_contract_jumpdest"),
            condition=Op.CALL(
                gas=Op.SUB(Op.GAS, 0x32),
                address=Op.MLOAD(offset=args_memory_offset),
                args_offset=0,
                args_size=0x20,
            ),
        )
        + Op.STOP
        + return_contract_code
    )
    initcode_1 = initcode_1_p1 + initcode_1_p2
    initcode_1.substitute(
        initcode_size=len(initcode_1),
        return_contract_jumpdest=len(initcode_1) - len(return_contract_code),
        callback_jumpdest=len(initcode_1_p1),
    )

    # Source: solidity
    # contract recursiveCreate2
    # {
    #     uint depp;
    #     function recursiveCreate2(address a, uint depth)
    #     {
    #         depth = depth - 1;
    #         depp = depth;
    #         if (depth > 0)
    #             recursiveCreate1 rec1 = new recursiveCreate1(a, depth);
    #     }
    # }

    args_memory_offset = len(initcode_1) + constructor_args_size
    address = Op.MLOAD(offset=args_memory_offset)
    depth = Op.SUB(Op.MLOAD(offset=args_memory_offset + 0x20), 1)
    initcode_2_p1 = (
        Op.CODECOPY(
            dest_offset=args_memory_offset,
            offset=Op.PUSH1(data_placeholder="calldata_offset"),
            size=constructor_args_size,
        )
        + Op.SSTORE(0, depth)
        + Op.JUMPI(
            pc=Op.PUSH1(data_placeholder="create_jumpdest"),
            condition=Op.GT(depth, 0),
        )
        + return_contract_code
    )
    initcode_2_p2 = (
        Op.JUMPDEST  # create jumpdest
        + Op.CODECOPY(
            dest_offset=0,
            offset=Op.PUSH1(data_placeholder="initcode_1_offset"),
            size=len(initcode_1),
        )
        + Op.MSTORE(
            offset=len(initcode_1),
            value=address,
        )
        + Op.MSTORE(
            offset=len(initcode_1) + 0x20,
            value=depth,
        )
        + Op.POP(
            Op.CREATE(
                value=0,
                offset=0,
                size=len(initcode_1) + constructor_args_size,
            )
        )
        + return_contract_code
    )
    initcode_2 = initcode_2_p1 + initcode_2_p2
    initcode_2.substitute(
        create_jumpdest=len(initcode_2_p1),
        initcode_1_offset=len(initcode_2),
        calldata_offset=len(initcode_2) + len(initcode_1),
    )

    # Source: solidity
    # contract main
    # {
    #     address maincontract;
    #     uint depp;
    #     function run(uint depth)
    #     {
    #         maincontract = 0x095e7baea6a6c7c4c2dfeb977efac326af552d87;
    #         depp = depth;
    #         recursiveCreate1 rec1 = new recursiveCreate1(maincontract,depth);
    #     }
    #
    #     function create2(uint depth)
    #     {
    #         recursiveCreate2 rec2 = new recursiveCreate2(maincontract,depth);
    #         address(rec2).send(2);
    #     }
    # }

    dispatcher = Op.JUMPI(
        pc=Op.PUSH2(data_placeholder="tx_entry_func_offset"),
        condition=Op.EQ(1, Op.CALLVALUE),
    )

    depth = Op.CALLDATALOAD(offset=0)

    # tx_entry_func -> initcode_1 -> re_entry_func -> initcode_2
    #                      ^                               |
    #                      |_______________________________|

    re_entry_func_p1 = (
        Op.JUMPDEST
        + Op.CODECOPY(
            dest_offset=0,
            offset=Op.PUSH2(data_placeholder="initcode_2_offset"),
            size=len(initcode_2) + len(initcode_1),
        )
        + Op.MSTORE(
            offset=len(initcode_2) + len(initcode_1),
            value=Op.ADDRESS,
        )
        + Op.MSTORE(
            offset=len(initcode_2) + len(initcode_1) + 0x20,
            value=depth,
        )
        + Op.JUMPI(
            pc=Op.PUSH2(data_placeholder="re_entry_func_send_ok_offset"),
            condition=Op.CALL(
                gas=0,
                address=Op.CREATE(
                    value=0,
                    offset=0,
                    size=len(initcode_2) + len(initcode_1) + 0x40,
                ),
                value=1,
            ),
        )
        + Op.INVALID  # Send fails
    )
    re_entry_func_p2 = Op.JUMPDEST + Op.RETURN(offset=0, size=0)
    re_entry_func = re_entry_func_p1 + re_entry_func_p2

    tx_entry_func = (
        Op.JUMPDEST
        + Op.SSTORE(0, Op.ADDRESS)
        + Op.SSTORE(1, depth)
        + Op.CODECOPY(
            dest_offset=0,
            offset=Op.PUSH2(data_placeholder="initcode_1_offset"),
            size=len(initcode_1),
        )
        + Op.MSTORE(
            offset=len(initcode_1),
            value=Op.ADDRESS,
        )
        + Op.MSTORE(
            offset=len(initcode_1) + 0x20,
            value=depth,
        )
        + Op.POP(
            Op.CREATE(
                value=0,
                offset=0,
                size=len(initcode_1) + 0x40,
            )
        )
        + Op.RETURN(offset=0, size=0)
    )

    factory_code = (
        dispatcher + re_entry_func + tx_entry_func + initcode_2 + initcode_1
    )

    jump_targets = {
        "re_entry_func_send_ok_offset": (
            len(dispatcher) + len(re_entry_func_p1)
        ),
        "tx_entry_func_offset": (len(dispatcher) + len(re_entry_func)),
    }

    initcode_2_offset = (
        len(dispatcher) + len(tx_entry_func) + len(re_entry_func)
    )
    initcode_1_offset = initcode_2_offset + len(initcode_2)
    factory_code.substitute(
        **jump_targets,
        initcode_2_offset=initcode_2_offset,
        initcode_1_offset=initcode_1_offset,
    )

    factory = pre.deploy_contract(code=factory_code, balance=0x20000000)

    max_depth = 772
    tx = Transaction(
        sender=sender,
        to=factory,
        data=Hash(max_depth),
        value=1,
    )

    post = {
        factory: Account(
            storage={0: factory, 1: max_depth},
        ),
        sender: Account(nonce=1),
        # Check only first created contract
        compute_create_address(address=factory, nonce=1): Account(
            storage={0: max_depth - 1}, nonce=1
        ),
    }

    state_test(pre=pre, post=post, tx=tx)
