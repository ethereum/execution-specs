"""
Contract B staticcalls contract A.
Contract A callcodes precompiled contracts.
It should execute successfully for each precompiled contract.


Ported from:
tests/static/state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml

callee code:
    push32 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c
    push1 0x00
    mstore
    push1 0x1c
    push1 0x20
    mstore
    push32 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f
    push1 0x40
    mstore
    push32 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549
    push1 0x60
    mstore
    push1 0x20
    push2 0x2000
    push1 0x80
    push1 0x00
    push1 0x00
    push1 0x01
    gas
    callcode
    ... (476 more instructions)

contract code:
    push32 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    push1 0x00
    sstore
    push3 0x012020
    push3 0x0a0000
    push1 0x00
    push1 0x00
    push20 0xa000000000000000000000000000000000000000
    gas
    staticcall
    pop
    push32 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    push1 0x01
    sstore
    push3 0x0a0000
    mload
    push2 0x0a00
    sstore
    push3 0x0b0000
    mload
    ... (163 more instructions)
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
    ["tests/static/state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_to_precompile_from_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Contract B staticcalls contract A.
Contract A callcodes precompiled contracts.
It should execute successfully for each precompiled contract.
."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    sender = Address("0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract = Address("0xb000000000000000000000000000000000000000")
    callee = Address("0xa000000000000000000000000000000000000000")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[callee] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH32[0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x1c] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x1] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa0000] + Op.MSTORE + Op.PUSH1[0xa0] + Op.PUSH1[0x2]
        + Op.EXP + Op.PUSH2[0x2000] + Op.MLOAD + Op.MOD + Op.PUSH3[0xa0100]
        + Op.MSTORE + Op.PUSH3[0xa0100] + Op.MLOAD + Op.ORIGIN + Op.EQ
        + Op.PUSH3[0xa0200] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH1[0x80] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x1] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb0000]
        + Op.MSTORE + Op.PUSH1[0xa0] + Op.PUSH1[0x2] + Op.EXP + Op.PUSH2[0x2020]
        + Op.MLOAD + Op.MOD + Op.PUSH3[0xb0100] + Op.MSTORE + Op.PUSH3[0xb0100]
        + Op.MLOAD + Op.ORIGIN + Op.EQ + Op.PUSH3[0xb0200] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x60]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE
        + Op.PUSH29[0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x2] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa0300] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH3[0xa0400] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa0500] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x2] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb0300]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH3[0xb0400] + Op.MSTORE
        + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xb0500] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE
        + Op.PUSH29[0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x3] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa0600] + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD
        + Op.PUSH3[0xa0700] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa0800] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x3] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb0600]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.MLOAD + Op.PUSH3[0xb0700] + Op.MSTORE
        + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xb0800] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE
        + Op.PUSH29[0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH1[0x20] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x4] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa0900] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa1000] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH1[0x20] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x4] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb0900]
        + Op.MSTORE + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xb1000] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2020]
        + Op.MSTORE + Op.PUSH1[0x1] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x20]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x3fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH32[0x2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc]
        + Op.PUSH1[0x80] + Op.MSTORE
        + Op.PUSH32[0x2f00000000000000000000000000000000000000000000000000000000000000]
        + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH1[0xa1] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x5] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa1100] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa1200] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH1[0xa1] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x5] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb1100]
        + Op.MSTORE + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xb1200] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x80] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0xa0] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x2020] + Op.MSTORE
        + Op.PUSH32[0xf25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba]
        + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4]
        + Op.PUSH1[0x60] + Op.MSTORE + Op.PUSH1[0x40] + Op.PUSH2[0x2000]
        + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x6] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa1300] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa1400] + Op.MSTORE + Op.PUSH2[0x2020] + Op.MLOAD
        + Op.PUSH3[0xa1500] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE + Op.PUSH1[0x40]
        + Op.PUSH2[0x3000] + Op.PUSH1[0x80] + Op.PUSH1[0x0] + Op.PUSH1[0x1]
        + Op.PUSH1[0x6] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb1300] + Op.MSTORE
        + Op.PUSH2[0x3000] + Op.MLOAD + Op.PUSH3[0xb1400] + Op.MSTORE
        + Op.PUSH2[0x3020] + Op.MLOAD + Op.PUSH3[0xb1500] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x60]
        + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x3000] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x3020] + Op.MSTORE
        + Op.PUSH32[0xf25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba]
        + Op.PUSH1[0x20] + Op.MSTORE + Op.PUSH1[0x3] + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH1[0x40] + Op.PUSH2[0x2000] + Op.PUSH1[0x60] + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.PUSH1[0x7] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xa1600]
        + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD + Op.PUSH3[0xa1700] + Op.MSTORE
        + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xa1800] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x2000] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE
        + Op.PUSH1[0x40] + Op.PUSH2[0x3000] + Op.PUSH1[0x60] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x7] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb1600]
        + Op.MSTORE + Op.PUSH2[0x3000] + Op.MLOAD + Op.PUSH3[0xb1700] + Op.MSTORE
        + Op.PUSH2[0x3020] + Op.MLOAD + Op.PUSH3[0xb1800] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH1[0x0] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH1[0x40] + Op.MSTORE + Op.PUSH1[0x0]
        + Op.PUSH2[0x3000] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x3020] + Op.MSTORE
        + Op.PUSH32[0x1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59]
        + Op.PUSH1[0x0] + Op.MSTORE
        + Op.PUSH32[0x3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41]
        + Op.PUSH1[0x20] + Op.MSTORE
        + Op.PUSH32[0x209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf7]
        + Op.PUSH1[0x40] + Op.MSTORE
        + Op.PUSH32[0x4bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678]
        + Op.PUSH1[0x60] + Op.MSTORE
        + Op.PUSH32[0x2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d]
        + Op.PUSH1[0x80] + Op.MSTORE
        + Op.PUSH32[0x120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550]
        + Op.PUSH1[0xa0] + Op.MSTORE
        + Op.PUSH32[0x111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c]
        + Op.PUSH1[0xc0] + Op.MSTORE
        + Op.PUSH32[0x2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411]
        + Op.PUSH1[0xe0] + Op.MSTORE
        + Op.PUSH32[0x198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2]
        + Op.PUSH2[0x100] + Op.MSTORE
        + Op.PUSH32[0x1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed]
        + Op.PUSH2[0x120] + Op.MSTORE
        + Op.PUSH32[0x90689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b]
        + Op.PUSH2[0x140] + Op.MSTORE
        + Op.PUSH32[0x12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa]
        + Op.PUSH2[0x160] + Op.MSTORE + Op.PUSH1[0x20] + Op.PUSH2[0x2000]
        + Op.PUSH2[0x180] + Op.PUSH1[0x0] + Op.PUSH1[0x0] + Op.PUSH1[0x8] + Op.GAS
        + Op.CALLCODE + Op.PUSH3[0xa1900] + Op.MSTORE + Op.PUSH2[0x2000] + Op.MLOAD
        + Op.PUSH3[0xa2000] + Op.MSTORE + Op.PUSH1[0x0] + Op.PUSH2[0x2000] + Op.MSTORE
        + Op.PUSH1[0x20] + Op.PUSH2[0x2020] + Op.PUSH2[0x180] + Op.PUSH1[0x0]
        + Op.PUSH1[0x1] + Op.PUSH1[0x8] + Op.GAS + Op.CALLCODE + Op.PUSH3[0xb1900]
        + Op.MSTORE + Op.PUSH2[0x2020] + Op.MLOAD + Op.PUSH3[0xb2000] + Op.MSTORE
        + Op.PUSH1[0x0] + Op.PUSH2[0x2020] + Op.MSTORE + Op.PUSH3[0x12020]
        + Op.PUSH3[0xa0000] + Op.RETURN + Op.STOP
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[contract] = Account(
        balance=1000,
        nonce=0,
        code=(
        Op.PUSH32[0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed]
        + Op.PUSH1[0x0] + Op.SSTORE + Op.PUSH3[0x12020] + Op.PUSH3[0xa0000]
        + Op.PUSH1[0x0] + Op.PUSH1[0x0]
        + Op.PUSH20[0xa000000000000000000000000000000000000000] + Op.GAS
        + Op.STATICCALL + Op.POP
        + Op.PUSH32[0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed]
        + Op.PUSH1[0x1] + Op.SSTORE + Op.PUSH3[0xa0000] + Op.MLOAD + Op.PUSH2[0xa00]
        + Op.SSTORE + Op.PUSH3[0xb0000] + Op.MLOAD + Op.PUSH2[0xb00] + Op.SSTORE
        + Op.PUSH3[0xa0100] + Op.MLOAD + Op.PUSH2[0xa01] + Op.SSTORE
        + Op.PUSH3[0xb0100] + Op.MLOAD + Op.PUSH2[0xb01] + Op.SSTORE
        + Op.PUSH3[0xa0200] + Op.MLOAD + Op.PUSH2[0xa02] + Op.SSTORE
        + Op.PUSH3[0xb0200] + Op.MLOAD + Op.PUSH2[0xb02] + Op.SSTORE
        + Op.PUSH3[0xa0300] + Op.MLOAD + Op.PUSH2[0xa03] + Op.SSTORE
        + Op.PUSH3[0xb0300] + Op.MLOAD + Op.PUSH2[0xb03] + Op.SSTORE
        + Op.PUSH3[0xa0400] + Op.MLOAD + Op.PUSH2[0xa04] + Op.SSTORE
        + Op.PUSH3[0xb0400] + Op.MLOAD + Op.PUSH2[0xb04] + Op.SSTORE
        + Op.PUSH3[0xa0500] + Op.MLOAD + Op.PUSH2[0xa05] + Op.SSTORE
        + Op.PUSH3[0xb0500] + Op.MLOAD + Op.PUSH2[0xb05] + Op.SSTORE
        + Op.PUSH3[0xa0600] + Op.MLOAD + Op.PUSH2[0xa06] + Op.SSTORE
        + Op.PUSH3[0xb0600] + Op.MLOAD + Op.PUSH2[0xb06] + Op.SSTORE
        + Op.PUSH3[0xa0700] + Op.MLOAD + Op.PUSH2[0xa07] + Op.SSTORE
        + Op.PUSH3[0xb0700] + Op.MLOAD + Op.PUSH2[0xb07] + Op.SSTORE
        + Op.PUSH3[0xa0800] + Op.MLOAD + Op.PUSH2[0xa08] + Op.SSTORE
        + Op.PUSH3[0xb0800] + Op.MLOAD + Op.PUSH2[0xb08] + Op.SSTORE
        + Op.PUSH3[0xa0900] + Op.MLOAD + Op.PUSH2[0xa09] + Op.SSTORE
        + Op.PUSH3[0xb0900] + Op.MLOAD + Op.PUSH2[0xb09] + Op.SSTORE
        + Op.PUSH3[0xa1000] + Op.MLOAD + Op.PUSH2[0xa10] + Op.SSTORE
        + Op.PUSH3[0xb1000] + Op.MLOAD + Op.PUSH2[0xb10] + Op.SSTORE
        + Op.PUSH3[0xa1100] + Op.MLOAD + Op.PUSH2[0xa11] + Op.SSTORE
        + Op.PUSH3[0xb1100] + Op.MLOAD + Op.PUSH2[0xb11] + Op.SSTORE
        + Op.PUSH3[0xa1200] + Op.MLOAD + Op.PUSH2[0xa12] + Op.SSTORE
        + Op.PUSH3[0xb1200] + Op.MLOAD + Op.PUSH2[0xb12] + Op.SSTORE
        + Op.PUSH3[0xa1300] + Op.MLOAD + Op.PUSH2[0xa13] + Op.SSTORE
        + Op.PUSH3[0xb1300] + Op.MLOAD + Op.PUSH2[0xb13] + Op.SSTORE
        + Op.PUSH3[0xa1400] + Op.MLOAD + Op.PUSH2[0xa14] + Op.SSTORE
        + Op.PUSH3[0xb1400] + Op.MLOAD + Op.PUSH2[0xb14] + Op.SSTORE
        + Op.PUSH3[0xa1500] + Op.MLOAD + Op.PUSH2[0xa15] + Op.SSTORE
        + Op.PUSH3[0xb1500] + Op.MLOAD + Op.PUSH2[0xb15] + Op.SSTORE
        + Op.PUSH3[0xa1600] + Op.MLOAD + Op.PUSH2[0xa16] + Op.SSTORE
        + Op.PUSH3[0xb1600] + Op.MLOAD + Op.PUSH2[0xb16] + Op.SSTORE
        + Op.PUSH3[0xa1700] + Op.MLOAD + Op.PUSH2[0xa17] + Op.SSTORE
        + Op.PUSH3[0xb1700] + Op.MLOAD + Op.PUSH2[0xb17] + Op.SSTORE
        + Op.PUSH3[0xa1800] + Op.MLOAD + Op.PUSH2[0xa18] + Op.SSTORE
        + Op.PUSH3[0xb1800] + Op.MLOAD + Op.PUSH2[0xb18] + Op.SSTORE
        + Op.PUSH3[0xa1900] + Op.MLOAD + Op.PUSH2[0xa19] + Op.SSTORE
        + Op.PUSH3[0xb1900] + Op.MLOAD + Op.PUSH2[0xb19] + Op.SSTORE
        + Op.PUSH3[0xa2000] + Op.MLOAD + Op.PUSH2[0xa20] + Op.SSTORE
        + Op.PUSH3[0xb2000] + Op.MLOAD + Op.PUSH2[0xb20] + Op.SSTORE + Op.STOP
    ),
        storage={0x0: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf, 0x1: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf},
    )

    tx = Transaction(
        secret_key=Hash(
            "0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8"
        ),
        to=contract,
        data=b"",
        gas_limit=4000000,
        gas_price=10,
        nonce=0,
        value=100,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
