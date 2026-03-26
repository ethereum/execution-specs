"""
Consensus issue test produced by fuzz testing team FuzzyVM-1240834021-1071009090.json.min

Ported from:
state_tests/stRandom2/randomStatetest649Filler.json
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
    ["state_tests/stRandom2/randomStatetest649Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest649(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Consensus issue test produced by fuzz testing team FuzzyVM-12408340..."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x61ec5e5029a151e121e39ae4d7546d549ea4b130f645f6f650ceec0416fe27f4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    # Source: raw
    # 0x7f6c756dbf65726963616e207f9439303733373936353331363631303037345a056000527f7265737582673075742074650041030a000000efbf7125e86c756dbf657269636020527f616e207f9439303733373936353331363631303037345a0572657375826730757f742074650041030a000000efbf7125e86c756dbf65726963616e207f943930377f33373936353331363631303037345a057265737582673075742074650041030a7cefbf7125e86c756dbf65726963616e207f9439303733373936353331367f3631303037345a057265737582673075742074650041030a000000efbf7125e8606c60e053607560e153606d60e25360bf60e353606560e453607260e553606960e653606360e75360e860006000f06000600060006000845a6950507f7f9439303733373936353331363631303037345a05726573758267307574207460005260206000f35b410061943961207f61616e616963616572600563012b9bbff167000000000000015f565b670000000000004ca65661363551613636556136555161363755613675516136385561369551613639556136b55161363a556136d55161363b556136f55161363c556137155161363d556137355161363e556137555161363f55613775516136405561379551613641556137b551613642556137d551613643556137f55161364455613815516136455561383551613646556138555161364755613875516136485561389551613649556138b55161364a556138d55161364b556138f55161364c556139155161364d556139355161364e556139555161364f55613975516136505561399551613651556139b551613652556139d551613653556139f55161365455613a155161365555613a355161365655613a555161365755613a755161365855613a955161365955613ab55161365a55613ad55161365b55613af55161365c00
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x6c756dbf65726963616e207f9439303733373936353331363631303037345a05)
        + Op.MSTORE(offset=0x20, value=0x7265737582673075742074650041030a000000efbf7125e86c756dbf65726963)
        + Op.PUSH32[0x616e207f9439303733373936353331363631303037345a057265737582673075]
        + Op.PUSH32[0x742074650041030a000000efbf7125e86c756dbf65726963616e207f94393037]
        + Op.PUSH32[0x33373936353331363631303037345a057265737582673075742074650041030a]
        + Op.PUSH29[0xefbf7125e86c756dbf65726963616e207f943930373337393635333136]
        + Op.PUSH32[0x3631303037345a057265737582673075742074650041030a000000efbf7125e8]
        + Op.MSTORE8(offset=0xe0, value=0x6c)
        + Op.MSTORE8(offset=0xe1, value=0x75)
        + Op.MSTORE8(offset=0xe2, value=0x6d)
        + Op.MSTORE8(offset=0xe3, value=0xbf)
        + Op.MSTORE8(offset=0xe4, value=0x65)
        + Op.MSTORE8(offset=0xe5, value=0x72)
        + Op.MSTORE8(offset=0xe6, value=0x69)
        + Op.MSTORE8(offset=0xe7, value=0x63)
        + Op.CREATE(value=0x0, offset=0x0, size=0xe8) + Op.PUSH1[0x0] * 4
        + Op.CODECOPY(dest_offset=0x50507f7f943930373337, offset=Op.GAS, size=Op.DUP5)
        + Op.CALLDATALOAD(offset=Op.CALLDATASIZE) + Op.BALANCE(address=Op.CALLER)
        + Op.CALLDATASIZE
        + Op.CALLDATACOPY(dest_offset=Op.ADDRESS, offset=Op.ADDRESS, size=Op.BALANCE(address=Op.CALLDATASIZE))
        + Op.SDIV(Op.GAS, Op.CALLVALUE)
        + Op.PUSH19[0x6573758267307574207460005260206000f35b] + Op.COINBASE
        + Op.STOP
        + Op.CALL(gas=0x12b9bbf, address=0x5, value=0x6572, args_offset=0x6963, args_size=0x616e, ret_offset=0x207f, ret_size=0x9439)
        + Op.JUMP(pc=Op.PUSH8[0x15f]) + Op.JUMPDEST
        + Op.JUMP(pc=Op.PUSH8[0x4ca6])
        + Op.SSTORE(key=0x3636, value=Op.MLOAD(offset=0x3635))
        + Op.SSTORE(key=0x3637, value=Op.MLOAD(offset=0x3655))
        + Op.SSTORE(key=0x3638, value=Op.MLOAD(offset=0x3675))
        + Op.SSTORE(key=0x3639, value=Op.MLOAD(offset=0x3695))
        + Op.SSTORE(key=0x363a, value=Op.MLOAD(offset=0x36b5))
        + Op.SSTORE(key=0x363b, value=Op.MLOAD(offset=0x36d5))
        + Op.SSTORE(key=0x363c, value=Op.MLOAD(offset=0x36f5))
        + Op.SSTORE(key=0x363d, value=Op.MLOAD(offset=0x3715))
        + Op.SSTORE(key=0x363e, value=Op.MLOAD(offset=0x3735))
        + Op.SSTORE(key=0x363f, value=Op.MLOAD(offset=0x3755))
        + Op.SSTORE(key=0x3640, value=Op.MLOAD(offset=0x3775))
        + Op.SSTORE(key=0x3641, value=Op.MLOAD(offset=0x3795))
        + Op.SSTORE(key=0x3642, value=Op.MLOAD(offset=0x37b5))
        + Op.SSTORE(key=0x3643, value=Op.MLOAD(offset=0x37d5))
        + Op.SSTORE(key=0x3644, value=Op.MLOAD(offset=0x37f5))
        + Op.SSTORE(key=0x3645, value=Op.MLOAD(offset=0x3815))
        + Op.SSTORE(key=0x3646, value=Op.MLOAD(offset=0x3835))
        + Op.SSTORE(key=0x3647, value=Op.MLOAD(offset=0x3855))
        + Op.SSTORE(key=0x3648, value=Op.MLOAD(offset=0x3875))
        + Op.SSTORE(key=0x3649, value=Op.MLOAD(offset=0x3895))
        + Op.SSTORE(key=0x364a, value=Op.MLOAD(offset=0x38b5))
        + Op.SSTORE(key=0x364b, value=Op.MLOAD(offset=0x38d5))
        + Op.SSTORE(key=0x364c, value=Op.MLOAD(offset=0x38f5))
        + Op.SSTORE(key=0x364d, value=Op.MLOAD(offset=0x3915))
        + Op.SSTORE(key=0x364e, value=Op.MLOAD(offset=0x3935))
        + Op.SSTORE(key=0x364f, value=Op.MLOAD(offset=0x3955))
        + Op.SSTORE(key=0x3650, value=Op.MLOAD(offset=0x3975))
        + Op.SSTORE(key=0x3651, value=Op.MLOAD(offset=0x3995))
        + Op.SSTORE(key=0x3652, value=Op.MLOAD(offset=0x39b5))
        + Op.SSTORE(key=0x3653, value=Op.MLOAD(offset=0x39d5))
        + Op.SSTORE(key=0x3654, value=Op.MLOAD(offset=0x39f5))
        + Op.SSTORE(key=0x3655, value=Op.MLOAD(offset=0x3a15))
        + Op.SSTORE(key=0x3656, value=Op.MLOAD(offset=0x3a35))
        + Op.SSTORE(key=0x3657, value=Op.MLOAD(offset=0x3a55))
        + Op.SSTORE(key=0x3658, value=Op.MLOAD(offset=0x3a75))
        + Op.SSTORE(key=0x3659, value=Op.MLOAD(offset=0x3a95))
        + Op.SSTORE(key=0x365a, value=Op.MLOAD(offset=0x3ab5))
        + Op.SSTORE(key=0x365b, value=Op.MLOAD(offset=0x3ad5))
        + Op.MLOAD(offset=0x3af5) + Op.PUSH2[0x365c] + Op.STOP,
        nonce=0,
        address=Address("0x39ab27391d04d35cae13dcdf2facaba711f0588f"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x3fffffffffffffff)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("756dbf65726963616e207f9439303733373936353331363631303037345a057265737582673075742074650041030a000000efbf7125e86c756dbf65726963616e207f9439303733373936353331363631303037345a0572657375826730757420746500"),  # noqa: E501
        gas_limit=147828,
        value=0xefbf7125,
        nonce=0,
        gas_price=10,
    )

    post = {sender: Account(nonce=1)}

    state_test(env=env, pre=pre, post=post, tx=tx)
