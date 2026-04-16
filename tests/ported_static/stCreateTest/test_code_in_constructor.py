"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stCreateTest/CodeInConstructorFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stCreateTest/CodeInConstructorFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_code_in_constructor(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0xBA5E0000BA5E0000BA5E0000BA5E0000BA5E0000)
    contract_0 = Address(0x000000000000000000000000000000000000DA7A)
    contract_1 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=4294967296,
    )

    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # {
    #     (def 'counterLoc 0)
    #     (def 'counterVal @@counterLoc)
    #     [[counterVal]] $0
    #     [[counterLoc]] (+ counterVal 1)
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=Op.SLOAD(key=0x0), value=Op.CALLDATALOAD(offset=0x0)
        )
        + Op.SSTORE(key=0x0, value=Op.ADD(Op.SLOAD(key=0x0), 0x1))
        + Op.STOP,
        storage={0: 1},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0x000000000000000000000000000000000000DA7A),  # noqa: E501
    )
    # Source: lll
    # {
    #   ; Variables are 0x20 bytes (= 256 bits) apart, except for
    #   ; code buffers that get 0x100 (256 bytes)
    #   (def 'constructorCode   0x000)
    #   (def 'contractCode      0x100)
    #   (def 'contractLength    0x200)
    #   (def 'constructorLength 0x220)
    #   (def 'addr              0x240)
    #   (def 'dataLoc           0x260)
    #   ; The type of CREATE to use
    #   (def 'createType        $ 4)
    #   ; Other constants
    #   (def 'NOP 0)   ; No OPeration
    #   ; Send data to 0x00da7a
    #   (def 'sendData (data) {
    #      [dataLoc] data
    #      (call 0xFFFFFF 0xda7a 0 dataLoc 0x20 0 0)
    #   })
    #   ; Buffer length (use for constructor and contract)
    #   (def 'bufLength     0x100)
    #   ;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;
    #   ; Create the contract and a constructor to pass to CREATE[2]
    #   ;
    #   ;
    #   [contractLength]
    #     (lll
    #       (sstore 0 0xFF)
    #       contractCode
    #     )
    #   [constructorLength]
    # ... (36 more lines)
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x6]
        + Op.CODECOPY(dest_offset=0x100, offset=Op.PUSH2[0x4C], size=Op.DUP1)
        + Op.PUSH2[0x200]
        + Op.MSTORE
        + Op.PUSH1[0xDB]
        + Op.CODECOPY(dest_offset=0x0, offset=Op.PUSH2[0x52], size=Op.DUP1)
        + Op.PUSH2[0x220]
        + Op.MSTORE
        + Op.JUMPI(pc=0x37, condition=Op.EQ(Op.CALLDATALOAD(offset=0x4), 0x1))
        + Op.CREATE2(
            value=0x0,
            offset=0x0,
            size=Op.ADD(0x100, Op.MLOAD(offset=0x200)),
            salt=0x5A17,
        )
        + Op.JUMP(pc=0x45)
        + Op.JUMPDEST
        + Op.CREATE(
            value=0x0, offset=0x0, size=Op.ADD(0x100, Op.MLOAD(offset=0x200))
        )
        + Op.JUMPDEST
        + Op.PUSH2[0x240]
        + Op.MSTORE
        + Op.STOP
        + Op.INVALID
        + Op.SSTORE(key=0x0, value=0xFF)
        + Op.STOP
        + Op.CODECOPY(dest_offset=0x100, offset=0x100, size=0x100)
        + Op.MSTORE(offset=0x260, value=Op.PC)
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x260, value=Op.ADDRESS)
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x260, value=Op.CODESIZE)
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x260, value=Op.EXTCODESIZE(address=Op.ADDRESS))
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.CODECOPY(dest_offset=0x100, offset=0x0, size=0x20)
        + Op.MSTORE(offset=0x260, value=Op.MLOAD(offset=0x100))
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.EXTCODECOPY(
            address=Op.ADDRESS, dest_offset=0x100, offset=0x0, size=0x20
        )
        + Op.MSTORE(offset=0x260, value=Op.MLOAD(offset=0x100))
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x260, value=Op.PC)
        + Op.POP(
            Op.CALL(
                gas=0xFFFFFF,
                address=contract_0,
                value=0x0,
                args_offset=0x260,
                args_size=0x20,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.RETURN(offset=0x100, size=Op.SUB(Op.CODESIZE, 0x100))
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=0,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 8,
                        1: 10,
                        2: compute_create_address(address=contract_1, nonce=0),
                        3: 262,
                        4: 0,
                        5: 0x610100610100610100395861026052600060006020610260600061DA7A62FFFF,  # noqa: E501
                        6: 0,
                        7: 184,
                    },
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                contract_0: Account(
                    storage={
                        0: 8,
                        1: 10,
                        2: 0x33C409678A4289F0184C95C627BA09DA2DAEAA46,
                        3: 262,
                        4: 0,
                        5: 0x610100610100610100395861026052600060006020610260600061DA7A62FFFF,  # noqa: E501
                        6: 0,
                        7: 184,
                    },
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx_data = [
        Bytes("83c7d758") + Hash(0x1),
        Bytes("83c7d758") + Hash(0x2),
    ]
    tx_gas = [9437184]

    tx = Transaction(
        sender=sender,
        to=contract_1,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
