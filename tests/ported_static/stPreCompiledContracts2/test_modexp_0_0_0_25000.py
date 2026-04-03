"""
Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompile,...

Ported from:
state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json
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
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/modexp_0_0_0_25000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="-g0",
        ),
        pytest.param(
            0,
            1,
            0,
            id="-g1",
        ),
        pytest.param(
            0,
            2,
            0,
            id="-g2",
        ),
        pytest.param(
            0,
            3,
            0,
            id="-g3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_0_0_0_25000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Puts the base 0, exponent 0 and modulus 0 into the MODEXP..."""
    coinbase = Address(0x3535353535353535353535353535353535353535)
    contract_0 = Address(0xC305C901078781C232A2A521C2AF7980F8385EE9)
    contract_1 = Address(0x0000000000000000000000000000000000000001)
    contract_2 = Address(0x0000000000000000000000000000000000000005)
    contract_3 = Address(0x0000000000000000000000000000000000000008)
    contract_4 = Address(0x0000000000000000000000000000000000000003)
    contract_5 = Address(0x0000000000000000000000000000000000000006)
    contract_6 = Address(0x0000000000000000000000000000000000000007)
    contract_7 = Address(0x0000000000000000000000000000000000000004)
    contract_8 = Address(0x0000000000000000000000000000000000000002)
    sender = EOA(
        key=0x44852B2A670ADE5407E78FB2863C51DE9FCB96542A07186FE3AEDA6BB8A116D
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xDE0B6B3A761FE12, nonce=1)
    # Source: hex
    # 0x600035601c52740100000000000000000000000000000000000000006020526fffffffffffffffffffffffffffffffff6040527fffffffffffffffffffffffffffffffff000000000000000000000000000000016060527402540be3fffffffffffffffffffffffffdabf41c006080527ffffffffffffffffffffffffdabf41c00000000000000000000000002540be40060a0526330c8d1da600051141561012b5760846004356004013511151558576004356004013560200160043560040161014037600161024061014051610160600060056305f5e0fff11558576001610220526102206021806102808284600060046015f150505061028080516020820120905060005561028060206020820352604081510160206001820306601f820103905060208203f350005b  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1C, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(
            offset=0x20, value=0x10000000000000000000000000000000000000000
        )
        + Op.MSTORE(offset=0x40, value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF)
        + Op.MSTORE(
            offset=0x60,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000000000000000000000000001,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x80, value=0x2540BE3FFFFFFFFFFFFFFFFFFFFFFFFFDABF41C00
        )
        + Op.MSTORE(
            offset=0xA0,
            value=0xFFFFFFFFFFFFFFFFFFFFFFFDABF41C00000000000000000000000002540BE400,  # noqa: E501
        )
        + Op.JUMPI(
            pc=0x12B,
            condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x0), 0x30C8D1DA)),
        )
        + Op.JUMPI(
            pc=Op.PC,
            condition=Op.ISZERO(
                Op.ISZERO(
                    Op.GT(
                        Op.CALLDATALOAD(
                            offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4))
                        ),
                        0x84,
                    )
                )
            ),
        )
        + Op.CALLDATACOPY(
            dest_offset=0x140,
            offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)),
            size=Op.ADD(
                0x20,
                Op.CALLDATALOAD(
                    offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4))
                ),
            ),
        )
        + Op.JUMPI(
            pc=Op.PC,
            condition=Op.ISZERO(
                Op.CALL(
                    gas=0x5F5E0FF,
                    address=0x5,
                    value=0x0,
                    args_offset=0x160,
                    args_size=Op.MLOAD(offset=0x140),
                    ret_offset=0x240,
                    ret_size=0x1,
                )
            ),
        )
        + Op.MSTORE(offset=0x220, value=0x1)
        + Op.PUSH2[0x220]
        + Op.PUSH1[0x21]
        + Op.POP(
            Op.CALL(
                gas=0x15,
                address=0x4,
                value=0x0,
                args_offset=Op.DUP5,
                args_size=Op.DUP3,
                ret_offset=0x280,
                ret_size=Op.DUP1,
            )
        )
        + Op.POP * 2
        + Op.PUSH2[0x280]
        + Op.SHA3(offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1))
        + Op.SWAP1
        + Op.POP
        + Op.PUSH1[0x0]
        + Op.SSTORE
        + Op.PUSH2[0x280]
        + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x20), value=0x20)
        + Op.ADD(Op.MLOAD(offset=Op.DUP2), 0x40)
        + Op.SUB(Op.ADD(Op.DUP3, 0x1F), Op.MOD(Op.SUB(Op.DUP3, 0x1), 0x20))
        + Op.SWAP1
        + Op.POP
        + Op.SUB(Op.DUP3, 0x20)
        + Op.RETURN
        + Op.POP
        + Op.STOP
        + Op.JUMPDEST,
        nonce=1,
        address=Address(0xC305C901078781C232A2A521C2AF7980F8385EE9),  # noqa: E501
    )
    # Source: hex
    # 0x
    coinbase = pre.deploy_contract(  # noqa: F841
        code="",
        balance=0x201EE,
        nonce=0,
        address=Address(0x3535353535353535353535353535353535353535),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_1 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000001),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_2 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000005),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_3 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000008),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_4 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000003),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_5 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000006),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_6 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000007),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_7 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000004),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_8 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=1,
        nonce=0,
        address=Address(0x0000000000000000000000000000000000000002),  # noqa: E501
    )

    tx_data = [
        Bytes("30c8d1da")
        + Hash(0x20)
        + Hash(0x60)
        + Hash(0x0)
        + Hash(0x0)
        + Hash(0x0),
    ]
    tx_gas = [47040, 90000, 110000, 200000]

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
    )

    post = {
        contract_1: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_0: Account(
            storage={
                0: 0xBC36789E7A1E281436464229828F817D6612F7B477D66591FF96A9E064BCC98A,  # noqa: E501
            },
            balance=0,
            nonce=1,
        ),
        contract_2: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_3: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_4: Account(storage={}, code=b"", balance=1, nonce=0),
        sender: Account(nonce=2),
        contract_5: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_6: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_7: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_8: Account(storage={}, code=b"", balance=1, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
