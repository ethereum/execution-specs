"""
Consensus issue test produced by fuzz testing team...

Ported from:
state_tests/stRandom2/randomStatetest649Filler.json
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stRandom2/randomStatetest649Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest649(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team..."""
    coinbase = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    sender = pre.fund_eoa(amount=0x3FFFFFFFFFFFFFFF)

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    # Source: raw
    # 0x7f6c756dbf65726963616e207f9439303733373936353331363631303037345a056000527f7265737582673075742074650041030a000000efbf7125e86c756dbf657269636020527f616e207f9439303733373936353331363631303037345a0572657375826730757f742074650041030a000000efbf7125e86c756dbf65726963616e207f943930377f33373936353331363631303037345a057265737582673075742074650041030a7cefbf7125e86c756dbf65726963616e207f9439303733373936353331367f3631303037345a057265737582673075742074650041030a000000efbf7125e8606c60e053607560e153606d60e25360bf60e353606560e453607260e553606960e653606360e75360e860006000f06000600060006000845a6950507f7f9439303733373936353331363631303037345a05726573758267307574207460005260206000f35b410061943961207f61616e616963616572600563012b9bbff167000000000000015f565b670000000000004ca65661363551613636556136555161363755613675516136385561369551613639556136b55161363a556136d55161363b556136f55161363c556137155161363d556137355161363e556137555161363f55613775516136405561379551613641556137b551613642556137d551613643556137f55161364455613815516136455561383551613646556138555161364755613875516136485561389551613649556138b55161364a556138d55161364b556138f55161364c556139155161364d556139355161364e556139555161364f55613975516136505561399551613651556139b551613652556139d551613653556139f55161365455613a155161365555613a355161365655613a555161365755613a755161365855613a955161365955613ab55161365a55613ad55161365b55613af55161365c00  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
            offset=0x0,
            value=0x6C756DBF65726963616E207F9439303733373936353331363631303037345A05,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x7265737582673075742074650041030A000000EFBF7125E86C756DBF65726963,  # noqa: E501
        )
        + Op.PUSH32[
            0x616E207F9439303733373936353331363631303037345A057265737582673075
        ]
        + Op.PUSH32[
            0x742074650041030A000000EFBF7125E86C756DBF65726963616E207F94393037
        ]
        + Op.PUSH32[
            0x33373936353331363631303037345A057265737582673075742074650041030A
        ]
        + Op.PUSH29[
            0xEFBF7125E86C756DBF65726963616E207F943930373337393635333136
        ]
        + Op.PUSH32[
            0x3631303037345A057265737582673075742074650041030A000000EFBF7125E8
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
        + Op.PUSH1[0x0] * 4
        + Op.CODECOPY(
            dest_offset=0x50507F7F943930373337, offset=Op.GAS, size=Op.DUP5
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
        + Op.STOP,
        nonce=0,
    )

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes("756dbf65")
        + Hash(
            0x726963616E207F9439303733373936353331363631303037345A057265737582
        )
        + Hash(
            0x673075742074650041030A000000EFBF7125E86C756DBF65726963616E207F94
        )
        + Hash(
            0x39303733373936353331363631303037345A0572657375826730757420746500
        ),
        gas_limit=147828,
        value=0xEFBF7125,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
