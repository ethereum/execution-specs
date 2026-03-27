"""
Test_create_oo_gafter_max_codesize.

Ported from:
state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml
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
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "a6f227c00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "a6f227c0000000000000000000000000000000000000000000000000000000000000000a000000000000000000000000000000000000000000000000000000000000000a0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000e",  # noqa: E501
    "a6f227c0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000010000000000000000000000000000000000000000000000000000000000000000",  # noqa: E501
    "a6f227c000000000000000000000000000000000000000000000000000000000000000fa00000000000000000000000000000000000000000000000000000000000000fa000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001ee",  # noqa: E501
]
TX_GAS = [4294967296]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CreateOOGafterMaxCodesizeFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="LowContractCount_NoDelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            1,
            0,
            0,
            id="LowContractCount_DelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            2,
            0,
            0,
            id="LowContractCount_DelegateCreate_CallCreate_SelfDestruct",
        ),
        pytest.param(
            3,
            0,
            0,
            id="HighContractCount_NoDelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            4,
            0,
            0,
            id="HighContractCount_DelegateCreate_CallCreateOOG",
        ),
        pytest.param(
            5,
            0,
            0,
            id="HighContractCount_DelegateCreate_CallCreate_SelfDestruct",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_create_oo_gafter_max_codesize(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_create_oo_gafter_max_codesize."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0x00000000000000000000000000000000000c0de0")
    contract_1 = Address("0x00000000000000000000000000000000000c0de1")
    contract_2 = Address("0x00000000000000000000000000000000000c0deb")
    contract_3 = Address("0x00000000000000000000000000000000000c0dea")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    # Source: yul
    # berlin
    # {
    #   // If calldata > 0, self-destruct, otherwise
    #   sstore(0, codesize())
    #   if gt(calldatasize(), 0) {
    #     selfdestruct(0)
    #   }
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.CODESIZE)
        + Op.JUMPI(pc=0xC, condition=Op.GT(Op.CALLDATASIZE, 0x0))
        + Op.STOP
        + Op.JUMPDEST
        + Op.SELFDESTRUCT(address=0x0),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000c0de0"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   // Init code that uses max codesize and can be called to selfdestruct
    #   let code_addr := 0x00000000000000000000000000000000000c0de0
    #   extcodecopy(code_addr, 0, 0, extcodesize(code_addr))
    #   return(0, 0x6000)
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH3[0xC0DE0]
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.EXTCODESIZE(address=Op.DUP3)
        + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.RETURN(offset=0x0, size=0x6000),
        nonce=0,
        address=Address("0x00000000000000000000000000000000000c0de1"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #   sstore (1, 1)
    #   let contract_count := calldataload(0)
    #   let should_oog := calldataload(32)
    #
    #   // get the init code that returns max codesize from another contract
    #   let initcode_addr := 0x00000000000000000000000000000000000c0de1
    #   let initcode_size := extcodesize(initcode_addr)
    #   extcodecopy(initcode_addr, 0, 0, initcode_size)
    #
    #   // create contracts with max codesize in loop
    #   for { let i := 0 } lt(i, contract_count) { i := add(i, 1) }
    #   {
    #       let address_created := create(0, 0, initcode_size)
    #       mstore( add(initcode_size, mul(i, 32)), address_created )
    #   }
    #   if gt(should_oog, 0) {
    #     invalid()
    #   }
    #   return(initcode_size, mul(contract_count, 32))
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=Op.DUP1, value=0x1)
        + Op.PUSH1[0x0]
        + Op.CALLDATALOAD(offset=Op.DUP1)
        + Op.CALLDATALOAD(offset=0x20)
        + Op.PUSH3[0xC0DE1]
        + Op.DUP4
        + Op.EXTCODESIZE(address=Op.DUP2)
        + Op.SWAP5
        + Op.DUP6
        + Op.SWAP3
        + Op.EXTCODECOPY
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x2D, condition=Op.LT(Op.DUP2, Op.DUP3))
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.JUMPI(pc=0x2B, condition=Op.LT)
        + Op.PUSH1[0x20]
        + Op.MUL
        + Op.SWAP1
        + Op.RETURN
        + Op.JUMPDEST
        + Op.INVALID
        + Op.JUMPDEST
        + Op.PUSH1[0x1]
        + Op.SWAP1
        + Op.MSTORE(
            offset=Op.ADD(Op.DUP7, Op.MUL(Op.DUP3, 0x20)),
            value=Op.CREATE(value=Op.DUP1, offset=0x0, size=Op.DUP5),
        )
        + Op.ADD
        + Op.JUMP(pc=0x18),
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0deb"),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #
    #   // Get the amount of contracts to create on this level
    #   let delegate_contract_count := calldataload(4)
    #
    #   // Get the amount of contracts to create on the sub level call
    #   let subcall_contract_count := calldataload(36)
    #
    #   // Get whether the subcall should oog
    #   let subcall_oog := calldataload(68)
    #
    #   // Get count of contracts to call to self-destruct
    #   let selfdestruct_count := calldataload(100)
    #
    #   // Delegate call for contract creation
    #   mstore(0, delegate_contract_count)
    #   mstore(32, 0)
    #   let returnStart := 64
    #   let returnLength := mul(delegate_contract_count, 32)
    #   let retcode := delegatecall(div(gas(), 2), 0x00000000000000000000000000000000000c0deb, 0, 64, returnStart, returnLength)  # noqa: E501
    #
    #   if eq(retcode, 0) {
    #     // We oog'd, fail test
    #     revert(0, 0)
    #   }
    #
    #   // Call for OOG contract creation
    #   mstore(0, subcall_contract_count)
    #   mstore(32, subcall_oog)
    # ... (31 more lines)
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLDATALOAD(offset=0x4)
        + Op.CALLDATALOAD(offset=0x24)
        + Op.CALLDATALOAD(offset=0x44)
        + Op.SWAP1
        + Op.CALLDATALOAD(offset=0x64)
        + Op.SWAP3
        + Op.MSTORE(offset=0x0, value=Op.DUP1)
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.PUSH1[0x0]
        + Op.PUSH1[0x40]
        + Op.MUL(Op.DUP4, 0x20)
        + Op.SWAP1
        + Op.PUSH1[0x40]
        + Op.DUP4
        + Op.PUSH3[0xC0DEB]
        + Op.JUMPI(
            pc=0xBF, condition=Op.EQ(Op.DELEGATECALL, Op.DIV(Op.GAS, 0x2))
        )
        + Op.MSTORE(offset=0x0, value=Op.DUP2)
        + Op.MSTORE(offset=0x20, value=Op.DUP3)
        + Op.PUSH1[0x0]
        + Op.ADD(0x40, Op.MUL(Op.DUP3, 0x20))
        + Op.MUL(Op.DUP5, 0x20)
        + Op.SWAP1
        + Op.PUSH1[0x40]
        + Op.DUP4
        + Op.DUP1
        + Op.PUSH3[0xC0DEB]
        + Op.JUMPI(pc=0xBA, condition=Op.EQ(Op.CALL, Op.DIV(Op.GAS, 0x2)))
        + Op.JUMPDEST
        + Op.PUSH1[0x0]
        + Op.DUP2
        + Op.SWAP4
        + Op.JUMPI(pc=0xB1, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.POP * 2
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x94, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.DUP3
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x77, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.STOP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.PUSH1[0x1]
        + Op.DUP2
        + Op.DUP1
        + Op.PUSH1[0x20]
        + Op.DUP4
        + Op.SWAP8
        + Op.MLOAD(offset=Op.ADD(0x40, Op.MUL))
        + Op.SUB(Op.GAS, 0x3E8)
        + Op.POP(Op.CALL)
        + Op.ADD
        + Op.JUMP(pc=0x6F)
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.PUSH1[0x20]
        + Op.PUSH1[0x1]
        + Op.SWAP8
        + Op.MLOAD(offset=Op.ADD(0x40, Op.MUL))
        + Op.SUB(Op.GAS, 0x3E8)
        + Op.POP(Op.CALL)
        + Op.ADD
        + Op.JUMP(pc=0x65)
        + Op.JUMPDEST
        + Op.ADD
        + Op.SWAP1
        + Op.POP
        + Op.CODESIZE
        + Op.DUP1
        + Op.JUMP(pc=0x60)
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x57, condition=Op.DUP3)
        + Op.JUMPDEST
        + Op.REVERT(offset=Op.DUP1, size=0x0),
        nonce=1,
        address=Address("0x00000000000000000000000000000000000c0dea"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": [0], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=1),
                contract_2: Account(storage={}, nonce=1),
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0xb3210b741a5dfbddc1636521965b3558defa3e60"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [1], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=11),
                contract_2: Account(storage={}, nonce=1),
                Address("0x396b47fae89161b1959b5a833acf816be526b860"): Account(
                    storage={0: 24576}
                ),
                Address("0xbd205415c24eb289b6a275baae74527b92b49fe2"): Account(
                    storage={0: 24576}
                ),
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0xb3210b741a5dfbddc1636521965b3558defa3e60"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [2], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=11),
                contract_2: Account(storage={1: 1}, nonce=11),
                Address(
                    "0x396b47fae89161b1959b5a833acf816be526b860"
                ): Account.NONEXISTENT,
                Address(
                    "0xbd205415c24eb289b6a275baae74527b92b49fe2"
                ): Account.NONEXISTENT,
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0x936d5e529580a9cc92bc2b2963a9d0a99f437e89"
                ): Account.NONEXISTENT,
                Address("0x2e5a5ec103443f6b299cf31a52c69cf222ae4e6b"): Account(
                    storage={0: 24576}
                ),
                Address("0xbade62b355fe6b7117f4f7c913321b318ca3a4da"): Account(
                    storage={0: 24576}
                ),
                Address("0xd8a8f3569a1d76027f9ece5010489576897014ea"): Account(
                    storage={0: 24576}
                ),
                Address("0xfcdccc3b46b9fbe71221061091e8fe82b77e02f2"): Account(
                    storage={0: 24576}
                ),
                Address("0x67262aa10552371ec665c2f90c56d9d65c16715e"): Account(
                    storage={0: 24576}
                ),
                Address("0xb3210b741a5dfbddc1636521965b3558defa3e60"): Account(
                    storage={0: 24576}
                ),
            },
        },
        {
            "indexes": {"data": [3], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=1),
                contract_2: Account(storage={}, nonce=1),
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0x782f34ee13897680a5000838ce53d07b9558b5e2"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [4], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=251),
                contract_2: Account(storage={}, nonce=1),
                Address("0x396b47fae89161b1959b5a833acf816be526b860"): Account(
                    storage={0: 24576}
                ),
                Address("0x336debb8ce5a3cf4b40be471ac04f77b51f2d2e1"): Account(
                    storage={0: 24576}
                ),
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0x782f34ee13897680a5000838ce53d07b9558b5e2"
                ): Account.NONEXISTENT,
            },
        },
        {
            "indexes": {"data": [5], "gas": -1, "value": -1},
            "network": [">=Cancun<Osaka"],
            "result": {
                contract_3: Account(storage={1: 1}, nonce=251),
                contract_2: Account(storage={1: 1}, nonce=251),
                Address(
                    "0x396b47fae89161b1959b5a833acf816be526b860"
                ): Account.NONEXISTENT,
                Address(
                    "0x336debb8ce5a3cf4b40be471ac04f77b51f2d2e1"
                ): Account.NONEXISTENT,
                Address(
                    "0x76e2310dc9277b22ffceb40d49229131674ebe02"
                ): Account.NONEXISTENT,
                Address(
                    "0x638e1b782452eaf5270509651f665d2c00e599ff"
                ): Account.NONEXISTENT,
                Address("0x511c6c5591eacfc8b9bf2658916225418508f548"): Account(
                    storage={0: 24576}
                ),
                Address("0x9ca6a1cfda677fc2679fce570dd47120686cb7c0"): Account(
                    storage={0: 24576}
                ),
                Address("0xdf7cd0b9839e4d93b98f09bf4c79366b9ffbe638"): Account(
                    storage={0: 24576}
                ),
                Address("0xee8b40edee25283a8c934b9c3a2ad8c848dc61b9"): Account(
                    storage={0: 24576}
                ),
                Address("0xe0fad4310f169961f052ac02bb70707ebfa3ece2"): Account(
                    storage={0: 24576}
                ),
                Address("0x782f34ee13897680a5000838ce53d07b9558b5e2"): Account(
                    storage={0: 24576}
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_3,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        gas_price=10,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
