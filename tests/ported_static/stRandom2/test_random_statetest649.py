"""
Consensus issue test produced by fuzz testing team...

Ported from:
tests/static/state_tests/stRandom2/randomStatetest649Filler.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["tests/static/state_tests/stRandom2/randomStatetest649Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest649(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x61EC5E5029A151E121E39AE4D7546D549EA4B130F645F6F650CEEC0416FE27F4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x6C756DBF65726963616E207F9439303733373936353331363631303037345A05,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0x7265737582673075742074650041030A000000EFBF7125E86C756DBF65726963,  # noqa: E501
            )
            + Op.PUSH32[
                0x616E207F9439303733373936353331363631303037345A057265737582673075  # noqa: E501
            ]
            + Op.PUSH32[
                0x742074650041030A000000EFBF7125E86C756DBF65726963616E207F94393037  # noqa: E501
            ]
            + Op.PUSH32[
                0x33373936353331363631303037345A057265737582673075742074650041030A  # noqa: E501
            ]
            + Op.PUSH29[
                0xEFBF7125E86C756DBF65726963616E207F943930373337393635333136
            ]
            + Op.PUSH32[
                0x3631303037345A057265737582673075742074650041030A000000EFBF7125E8  # noqa: E501
            ]
            + Op.MSTORE8(offset=0xE0, value=0x6C)
            + Op.MSTORE8(offset=0xE1, value=0x75)
            + Op.MSTORE8(offset=0xE2, value=0x6D)
            + Op.MSTORE8(offset=0xE3, value=0xBF)
            + Op.MSTORE8(offset=0xE4, value=0x65)
            + Op.MSTORE8(offset=0xE5, value=0x72)
            + Op.MSTORE8(offset=0xE6, value=0x69)
            + Op.MSTORE8(offset=0xE7, value=0x63)
            + Op.CREATE(value=0x0, offset=0x0, size=0xE8)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.CODECOPY(
                dest_offset=0x50507F7F943930373337,
                offset=Op.GAS,
                size=Op.DUP5,
            )
            + Op.CALLDATALOAD(offset=Op.CALLDATASIZE)
            + Op.BALANCE(address=Op.CALLER)
            + Op.CALLDATASIZE
            + Op.CALLDATACOPY(
                dest_offset=Op.ADDRESS,
                offset=Op.ADDRESS,
                size=Op.BALANCE(address=Op.CALLDATASIZE),
            )
            + Op.SDIV(Op.GAS, Op.CALLVALUE)
            + Op.PUSH19[0x6573758267307574207460005260206000F35B]
            + Op.COINBASE
            + Op.STOP
            + Op.CALL(
                gas=0x12B9BBF,
                address=0x5,
                value=0x6572,
                args_offset=0x6963,
                args_size=0x616E,
                ret_offset=0x207F,
                ret_size=0x9439,
            )
            + Op.JUMP(pc=Op.PUSH8[0x15F])
            + Op.JUMPDEST
            + Op.JUMP(pc=Op.PUSH8[0x4CA6])
            + Op.SSTORE(key=0x3636, value=Op.MLOAD(offset=0x3635))
            + Op.SSTORE(key=0x3637, value=Op.MLOAD(offset=0x3655))
            + Op.SSTORE(key=0x3638, value=Op.MLOAD(offset=0x3675))
            + Op.SSTORE(key=0x3639, value=Op.MLOAD(offset=0x3695))
            + Op.SSTORE(key=0x363A, value=Op.MLOAD(offset=0x36B5))
            + Op.SSTORE(key=0x363B, value=Op.MLOAD(offset=0x36D5))
            + Op.SSTORE(key=0x363C, value=Op.MLOAD(offset=0x36F5))
            + Op.SSTORE(key=0x363D, value=Op.MLOAD(offset=0x3715))
            + Op.SSTORE(key=0x363E, value=Op.MLOAD(offset=0x3735))
            + Op.SSTORE(key=0x363F, value=Op.MLOAD(offset=0x3755))
            + Op.SSTORE(key=0x3640, value=Op.MLOAD(offset=0x3775))
            + Op.SSTORE(key=0x3641, value=Op.MLOAD(offset=0x3795))
            + Op.SSTORE(key=0x3642, value=Op.MLOAD(offset=0x37B5))
            + Op.SSTORE(key=0x3643, value=Op.MLOAD(offset=0x37D5))
            + Op.SSTORE(key=0x3644, value=Op.MLOAD(offset=0x37F5))
            + Op.SSTORE(key=0x3645, value=Op.MLOAD(offset=0x3815))
            + Op.SSTORE(key=0x3646, value=Op.MLOAD(offset=0x3835))
            + Op.SSTORE(key=0x3647, value=Op.MLOAD(offset=0x3855))
            + Op.SSTORE(key=0x3648, value=Op.MLOAD(offset=0x3875))
            + Op.SSTORE(key=0x3649, value=Op.MLOAD(offset=0x3895))
            + Op.SSTORE(key=0x364A, value=Op.MLOAD(offset=0x38B5))
            + Op.SSTORE(key=0x364B, value=Op.MLOAD(offset=0x38D5))
            + Op.SSTORE(key=0x364C, value=Op.MLOAD(offset=0x38F5))
            + Op.SSTORE(key=0x364D, value=Op.MLOAD(offset=0x3915))
            + Op.SSTORE(key=0x364E, value=Op.MLOAD(offset=0x3935))
            + Op.SSTORE(key=0x364F, value=Op.MLOAD(offset=0x3955))
            + Op.SSTORE(key=0x3650, value=Op.MLOAD(offset=0x3975))
            + Op.SSTORE(key=0x3651, value=Op.MLOAD(offset=0x3995))
            + Op.SSTORE(key=0x3652, value=Op.MLOAD(offset=0x39B5))
            + Op.SSTORE(key=0x3653, value=Op.MLOAD(offset=0x39D5))
            + Op.SSTORE(key=0x3654, value=Op.MLOAD(offset=0x39F5))
            + Op.SSTORE(key=0x3655, value=Op.MLOAD(offset=0x3A15))
            + Op.SSTORE(key=0x3656, value=Op.MLOAD(offset=0x3A35))
            + Op.SSTORE(key=0x3657, value=Op.MLOAD(offset=0x3A55))
            + Op.SSTORE(key=0x3658, value=Op.MLOAD(offset=0x3A75))
            + Op.SSTORE(key=0x3659, value=Op.MLOAD(offset=0x3A95))
            + Op.SSTORE(key=0x365A, value=Op.MLOAD(offset=0x3AB5))
            + Op.SSTORE(key=0x365B, value=Op.MLOAD(offset=0x3AD5))
            + Op.MLOAD(offset=0x3AF5)
            + Op.PUSH2[0x365C]
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x39ab27391d04d35cae13dcdf2facaba711f0588f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3FFFFFFFFFFFFFFF)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "756dbf65726963616e207f9439303733373936353331363631303037345a057265737582"  # noqa: E501
            "673075742074650041030a000000efbf7125e86c756dbf65726963616e207f9439303733"  # noqa: E501
            "373936353331363631303037345a0572657375826730757420746500"
        ),
        gas_limit=147828,
        value=4022300965,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
