"""
Consensus issue test produced by fuzz testing team FuzzyVM-1240834021-1071009090.json.min

Ported from:
tests/static/state_tests/stRandom2/randomStatetest649Filler.json

contract code:
    push32 0x6c756dbf65726963616e207f9439303733373936353331363631303037345a05
    push1 0x00
    mstore
    push32 0x7265737582673075742074650041030a000000efbf7125e86c756dbf65726963
    push1 0x20
    mstore
    push32 0x616e207f9439303733373936353331363631303037345a057265737582673075
    push32 0x742074650041030a000000efbf7125e86c756dbf65726963616e207f94393037
    push32 0x33373936353331363631303037345a057265737582673075742074650041030a
    push29 0xefbf7125e86c756dbf65726963616e207f943930373337393635333136
    push32 0x3631303037345a057265737582673075742074650041030a000000efbf7125e8
    push1 0x6c
    push1 0xe0
    mstore8
    push1 0x75
    push1 0xe1
    mstore8
    push1 0x6d
    push1 0xe2
    mstore8
    ... (212 more instructions)
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Environment,
    Hash,
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
    """Consensus issue test produced by fuzz testing team FuzzyVM-1240834021-1071009090.json.min."""
    coinbase = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = Address("0x7bb14be81eb9266df1c09994a1bc1d483057d3f0")
    contract = Address("0x39ab27391d04d35cae13dcdf2facaba711f0588f")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10944489199640098,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.PUSH32[0x6c756dbf65726963616e207f9439303733373936353331363631303037345a05]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x7265737582673075742074650041030a000000efbf7125e86c756dbf65726963]
        + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x616e207f9439303733373936353331363631303037345a057265737582673075]
        + Op.PUSH32[0x742074650041030a000000efbf7125e86c756dbf65726963616e207f94393037]
        + Op.PUSH32[0x33373936353331363631303037345a057265737582673075742074650041030a]
        + Op.PUSH29[0xefbf7125e86c756dbf65726963616e207f943930373337393635333136]
        + Op.PUSH32[0x3631303037345a057265737582673075742074650041030a000000efbf7125e8]
        + Op.PUSH1[0x6c] + Op.PUSH1[0xe0] + Op.MSTORE8 + Op.PUSH1[0x75]
        + Op.PUSH1[0xe1] + Op.MSTORE8 + Op.PUSH1[0x6d] + Op.PUSH1[0xe2] + Op.MSTORE8
        + Op.PUSH1[0xbf] + Op.PUSH1[0xe3] + Op.MSTORE8 + Op.PUSH1[0x65]
        + Op.PUSH1[0xe4] + Op.MSTORE8 + Op.PUSH1[0x72] + Op.PUSH1[0xe5] + Op.MSTORE8
        + Op.PUSH1[0x69] + Op.PUSH1[0xe6] + Op.MSTORE8 + Op.PUSH1[0x63]
        + Op.PUSH1[0xe7] + Op.MSTORE8 + Op.PUSH1[0xe8] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.CREATE + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.DUP5 + Op.GAS + Op.PUSH10[0x50507f7f943930373337] + Op.CODECOPY
        + Op.CALLDATASIZE + Op.CALLDATALOAD + Op.CALLER + Op.BALANCE + Op.CALLDATASIZE
        + Op.CALLDATASIZE + Op.BALANCE + Op.ADDRESS + Op.ADDRESS + Op.CALLDATACOPY
        + Op.CALLVALUE + Op.GAS + Op.SDIV
        + Op.PUSH19[0x6573758267307574207460005260206000f35b] + Op.COINBASE + Op.STOP
        + Op.PUSH2[0x9439] + Op.PUSH2[0x207f] + Op.PUSH2[0x616e] + Op.PUSH2[0x6963]
        + Op.PUSH2[0x6572] + Op.PUSH1[0x5] + Op.PUSH4[0x12b9bbf] + Op.CALL
        + Op.PUSH8[0x15f] + Op.JUMP + Op.JUMPDEST + Op.PUSH8[0x4ca6] + Op.JUMP
        + Op.PUSH2[0x3635] + Op.MLOAD + Op.PUSH2[0x3636] + Op.SSTORE
        + Op.PUSH2[0x3655] + Op.MLOAD + Op.PUSH2[0x3637] + Op.SSTORE
        + Op.PUSH2[0x3675] + Op.MLOAD + Op.PUSH2[0x3638] + Op.SSTORE
        + Op.PUSH2[0x3695] + Op.MLOAD + Op.PUSH2[0x3639] + Op.SSTORE
        + Op.PUSH2[0x36b5] + Op.MLOAD + Op.PUSH2[0x363a] + Op.SSTORE
        + Op.PUSH2[0x36d5] + Op.MLOAD + Op.PUSH2[0x363b] + Op.SSTORE
        + Op.PUSH2[0x36f5] + Op.MLOAD + Op.PUSH2[0x363c] + Op.SSTORE
        + Op.PUSH2[0x3715] + Op.MLOAD + Op.PUSH2[0x363d] + Op.SSTORE
        + Op.PUSH2[0x3735] + Op.MLOAD + Op.PUSH2[0x363e] + Op.SSTORE
        + Op.PUSH2[0x3755] + Op.MLOAD + Op.PUSH2[0x363f] + Op.SSTORE
        + Op.PUSH2[0x3775] + Op.MLOAD + Op.PUSH2[0x3640] + Op.SSTORE
        + Op.PUSH2[0x3795] + Op.MLOAD + Op.PUSH2[0x3641] + Op.SSTORE
        + Op.PUSH2[0x37b5] + Op.MLOAD + Op.PUSH2[0x3642] + Op.SSTORE
        + Op.PUSH2[0x37d5] + Op.MLOAD + Op.PUSH2[0x3643] + Op.SSTORE
        + Op.PUSH2[0x37f5] + Op.MLOAD + Op.PUSH2[0x3644] + Op.SSTORE
        + Op.PUSH2[0x3815] + Op.MLOAD + Op.PUSH2[0x3645] + Op.SSTORE
        + Op.PUSH2[0x3835] + Op.MLOAD + Op.PUSH2[0x3646] + Op.SSTORE
        + Op.PUSH2[0x3855] + Op.MLOAD + Op.PUSH2[0x3647] + Op.SSTORE
        + Op.PUSH2[0x3875] + Op.MLOAD + Op.PUSH2[0x3648] + Op.SSTORE
        + Op.PUSH2[0x3895] + Op.MLOAD + Op.PUSH2[0x3649] + Op.SSTORE
        + Op.PUSH2[0x38b5] + Op.MLOAD + Op.PUSH2[0x364a] + Op.SSTORE
        + Op.PUSH2[0x38d5] + Op.MLOAD + Op.PUSH2[0x364b] + Op.SSTORE
        + Op.PUSH2[0x38f5] + Op.MLOAD + Op.PUSH2[0x364c] + Op.SSTORE
        + Op.PUSH2[0x3915] + Op.MLOAD + Op.PUSH2[0x364d] + Op.SSTORE
        + Op.PUSH2[0x3935] + Op.MLOAD + Op.PUSH2[0x364e] + Op.SSTORE
        + Op.PUSH2[0x3955] + Op.MLOAD + Op.PUSH2[0x364f] + Op.SSTORE
        + Op.PUSH2[0x3975] + Op.MLOAD + Op.PUSH2[0x3650] + Op.SSTORE
        + Op.PUSH2[0x3995] + Op.MLOAD + Op.PUSH2[0x3651] + Op.SSTORE
        + Op.PUSH2[0x39b5] + Op.MLOAD + Op.PUSH2[0x3652] + Op.SSTORE
        + Op.PUSH2[0x39d5] + Op.MLOAD + Op.PUSH2[0x3653] + Op.SSTORE
        + Op.PUSH2[0x39f5] + Op.MLOAD + Op.PUSH2[0x3654] + Op.SSTORE
        + Op.PUSH2[0x3a15] + Op.MLOAD + Op.PUSH2[0x3655] + Op.SSTORE
        + Op.PUSH2[0x3a35] + Op.MLOAD + Op.PUSH2[0x3656] + Op.SSTORE
        + Op.PUSH2[0x3a55] + Op.MLOAD + Op.PUSH2[0x3657] + Op.SSTORE
        + Op.PUSH2[0x3a75] + Op.MLOAD + Op.PUSH2[0x3658] + Op.SSTORE
        + Op.PUSH2[0x3a95] + Op.MLOAD + Op.PUSH2[0x3659] + Op.SSTORE
        + Op.PUSH2[0x3ab5] + Op.MLOAD + Op.PUSH2[0x365a] + Op.SSTORE
        + Op.PUSH2[0x3ad5] + Op.MLOAD + Op.PUSH2[0x365b] + Op.SSTORE
        + Op.PUSH2[0x3af5] + Op.MLOAD + Op.PUSH2[0x365c] + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0x3fffffffffffffff, nonce=0)

    tx = Transaction(
        secret_key=Hash(
            "0x61ec5e5029a151e121e39ae4d7546d549ea4b130f645f6f650ceec0416fe27f4"
        ),
        to=contract,
        data=bytes.fromhex(
            "756dbf65726963616e207f9439303733373936353331363631303037345a057265737582"
            "673075742074650041030a000000efbf7125e86c756dbf65726963616e207f9439303733"
            "373936353331363631303037345a0572657375826730757420746500"
        ),
        gas_limit=147828,
        gas_price=10,
        nonce=0,
        value=4022300965,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
