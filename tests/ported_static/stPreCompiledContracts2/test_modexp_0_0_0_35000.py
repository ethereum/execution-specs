"""
Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompile, saves the hash of the result. Gives the execution 35000 gas

Ported from:
state_tests/stPreCompiledContracts2/modexp_0_0_0_35000Filler.json
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
from execution_testing.vm import Op
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000060000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
]
TX_GAS = [57040, 90000, 110000, 200000]
TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d])


@pytest.mark.ported_from(
    ["state_tests/stPreCompiledContracts2/modexp_0_0_0_35000Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0, 0, 0,
            id="-g0",
        ),
        pytest.param(
            0, 1, 0,
            id="-g1",
        ),
        pytest.param(
            0, 2, 0,
            id="-g2",
        ),
        pytest.param(
            0, 3, 0,
            id="-g3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_modexp_0_0_0_35000(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Puts the base 0, exponent 0 and modulus 0 into the MODEXP precompil..."""
    coinbase = Address("0x3535353535353535353535353535353535353535")
    contract_0 = Address("0xc305c901078781c232a2a521c2af7980f8385ee9")
    contract_1 = Address("0x0000000000000000000000000000000000000001")
    contract_2 = Address("0x0000000000000000000000000000000000000005")
    contract_3 = Address("0x0000000000000000000000000000000000000008")
    contract_4 = Address("0x0000000000000000000000000000000000000003")
    contract_5 = Address("0x0000000000000000000000000000000000000006")
    contract_6 = Address("0x0000000000000000000000000000000000000007")
    contract_7 = Address("0x0000000000000000000000000000000000000004")
    contract_8 = Address("0x0000000000000000000000000000000000000002")
    sender = EOA(
        key=0x44852b2a670ade5407e78fb2863c51de9fcb96542a07186fe3aeda6bb8a116d
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[sender] = Account(balance=0xde0b6b3a761fe12, nonce=1)
    # Source: hex
    # 0x600035601c52740100000000000000000000000000000000000000006020526fffffffffffffffffffffffffffffffff6040527fffffffffffffffffffffffffffffffff000000000000000000000000000000016060527402540be3fffffffffffffffffffffffffdabf41c006080527ffffffffffffffffffffffffdabf41c00000000000000000000000002540be40060a0526330c8d1da600051141561012b5760846004356004013511151558576004356004013560200160043560040161014037600161024061014051610160600060056305f5e0fff11558576001610220526102206021806102808284600060046015f150505061028080516020820120905060005561028060206020820352604081510160206001820306601f820103905060208203f350005b
    contract_0 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x1c, value=Op.CALLDATALOAD(offset=0x0))
        + Op.MSTORE(offset=0x20, value=0x10000000000000000000000000000000000000000)
        + Op.MSTORE(offset=0x40, value=0xffffffffffffffffffffffffffffffff)
        + Op.MSTORE(offset=0x60, value=0xffffffffffffffffffffffffffffffff00000000000000000000000000000001)
        + Op.MSTORE(offset=0x80, value=0x2540be3fffffffffffffffffffffffffdabf41c00)
        + Op.MSTORE(offset=0xa0, value=0xfffffffffffffffffffffffdabf41c00000000000000000000000002540be400)
        + Op.JUMPI(pc=0x12b, condition=Op.ISZERO(Op.EQ(Op.MLOAD(offset=0x0), 0x30c8d1da)))
        + Op.JUMPI(pc=Op.PC, condition=Op.ISZERO(Op.ISZERO(Op.GT(Op.CALLDATALOAD(offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4))), 0x84))))
        + Op.CALLDATACOPY(dest_offset=0x140, offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)), size=Op.ADD(0x20, Op.CALLDATALOAD(offset=Op.ADD(0x4, Op.CALLDATALOAD(offset=0x4)))))
        + Op.JUMPI(pc=Op.PC, condition=Op.ISZERO(Op.CALL(gas=0x5f5e0ff, address=0x5, value=0x0, args_offset=0x160, args_size=Op.MLOAD(offset=0x140), ret_offset=0x240, ret_size=0x1)))
        + Op.MSTORE(offset=0x220, value=0x1) + Op.PUSH2[0x220] + Op.PUSH1[0x21]
        + Op.POP(Op.CALL(gas=0x15, address=0x4, value=0x0, args_offset=Op.DUP5, args_size=Op.DUP3, ret_offset=0x280, ret_size=Op.DUP1))
        + Op.POP * 2 + Op.PUSH2[0x280]
        + Op.SHA3(offset=Op.ADD(Op.DUP3, 0x20), size=Op.MLOAD(offset=Op.DUP1))
        + Op.SWAP1 + Op.POP + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH2[0x280]
        + Op.MSTORE(offset=Op.SUB(Op.DUP3, 0x20), value=0x20)
        + Op.ADD(Op.MLOAD(offset=Op.DUP2), 0x40)
        + Op.SUB(Op.ADD(Op.DUP3, 0x1f), Op.MOD(Op.SUB(Op.DUP3, 0x1), 0x20))
        + Op.SWAP1 + Op.POP + Op.SUB(Op.DUP3, 0x20) + Op.RETURN + Op.POP
        + Op.STOP + Op.JUMPDEST,
        nonce=1,
        address=Address("0xc305c901078781c232a2a521c2af7980f8385ee9"),  # noqa: E501
    )
    # Source: hex
    # 0x
    coinbase = pre.deploy_contract(
        code="",
        balance=0x201ee,
        nonce=0,
        address=Address("0x3535353535353535353535353535353535353535"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_1 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_2 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000005"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_3 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000008"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_4 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000003"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_5 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000006"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_6 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000007"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_7 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000004"),  # noqa: E501
    )
    # Source: hex
    # 0x
    contract_8 = pre.deploy_contract(
        code="",
        balance=1,
        nonce=0,
        address=Address("0x0000000000000000000000000000000000000002"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {'data': 0, 'gas': -1, 'value': 0},
            "network": ['>=Cancun'],
            "result": {
        contract_1: Account(storage={}, code=b"", balance=1, nonce=0),
        contract_0: Account(
                storage={
            0: 0xbc36789e7a1e281436464229828f817d6612f7b477d66591ff96a9e064bcc98a,
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
    },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        nonce=1,
        gas_price=10,
        error=_exc,
    )


    state_test(env=env, pre=pre, post=post, tx=tx)
