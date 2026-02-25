"""
Ported from:
tests/static/state_tests/stRandom/randomStatetest48Filler.json

contract code:
    codesize
    push25 0x5231d8e75db11d6da7040cee1a12ebf739e5022caa60f92d51
    push4 0x6060b6d9
    push14 0x698fc0e9ced2f6a0087344559c43
    push2 0x2f05
    push2 0xa73b
    log3
    push1 0x0a
    push1 0x0d
    push1 0x14
    push1 0x09
    push4 0x186262c1
    push20 0x292e762689b448debe7899ade7acb27a84a85c44
    push4 0x70f82d9f
    call
    push1 0x41
    push7 0xf49ef1fea120af
    push24 0xba4cce3f35bc52ca5c40bf14c77e95ea92e69520143ff9c7
    dup3
    push28 0xcfe760aee06d241e31a0773476da22f7ce8131475838c23b59f7a3c4
    ... (5 more instructions)

coinbase code:
    push1 0x00
    calldataload
    sload
    iszero
    push1 0x09
    jumpi
    stop
    jumpdest
    push1 0x20
    calldataload
    push1 0x00
    calldataload
    sstore
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
    ["tests/static/state_tests/stRandom/randomStatetest48Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest48(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = Address("0x2e3d0156d2b99a6eacba540c55f423c8f5a33143")
    contract = Address("0x292e762689b448debe7899ade7acb27a84a85c44")

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[contract] = Account(
        balance=0,
        nonce=0,
        code=(
        Op.CODESIZE
        + Op.PUSH25[0x5231d8e75db11d6da7040cee1a12ebf739e5022caa60f92d51]
        + Op.PUSH4[0x6060b6d9] + Op.PUSH14[0x698fc0e9ced2f6a0087344559c43]
        + Op.PUSH2[0x2f05] + Op.PUSH2[0xa73b] + Op.LOG3 + Op.PUSH1[0xa]
        + Op.PUSH1[0xd] + Op.PUSH1[0x14] + Op.PUSH1[0x9] + Op.PUSH4[0x186262c1]
        + Op.PUSH20[0x292e762689b448debe7899ade7acb27a84a85c44] + Op.PUSH4[0x70f82d9f]
        + Op.CALL + Op.PUSH1[0x41] + Op.PUSH7[0xf49ef1fea120af]
        + Op.PUSH24[0xba4cce3f35bc52ca5c40bf14c77e95ea92e69520143ff9c7] + Op.DUP3
        + Op.PUSH28[0xcfe760aee06d241e31a0773476da22f7ce8131475838c23b59f7a3c4]
        + Op.PUSH12[0x2b99c0955e169ee3527ca9f7] + Op.PUSH8[0x4467bdf2c0eebf6f]
        + Op.PUSH1[0x12] + Op.SWAP3 + Op.ORIGIN
    ),
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=0)
    pre[coinbase] = Account(
        balance=46,
        nonce=0,
        code=(
        Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SLOAD + Op.ISZERO + Op.PUSH1[0x9]
        + Op.JUMPI + Op.STOP + Op.JUMPDEST + Op.PUSH1[0x20] + Op.CALLDATALOAD
        + Op.PUSH1[0x0] + Op.CALLDATALOAD + Op.SSTORE
    ),
    )

    tx = Transaction(
        secret_key=Hash(
            "0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005"
        ),
        to=contract,
        data=bytes.fromhex(
            "76dd12f3185b84dfc71eb93f4df4ca30dcf34446f25793016424a5e33b6a65fb5d64a939"
            "4d7ebefb1c15de971a2d2f53377765d50c698d4e26adea05dd2f6a1688f60eb8b172d796"
            "a45c6f79596bfb719df5a571ce8c339e9d7e9b3905324643a2b9fd541956552fc258e688"
            "303ecb25082776fde7334cdf046f70c8669a6a05c36909038278e925f0156be9ddb9b837"
            "86de8a325ab28e61d18397714bcda0fd5ca879c870d383721c638733b1f78074cc1079e7"
            "2e0bbbad262348a8976eaaf313a261dccb69dbaf283beebcac7ac3b8166a4deb1fe5099a"
            "1c7f3ef595357e76ca260a703bec4848a3cc9804d6de6e5b853b54dd65979292f596ee13"
            "2edf67eb948e4e4d22f9cb7629bf8b642cb921b2ed9b13e47cb06d6c6f4384c7b372ee7c"
            "b61f76a363f8fa68309e3d308179ad3e15fd752d6586e9030c8c1f274878bf7fbe1b5699"
            "44fdda166c47411878f3702bbe1bbabbce8b10701076e0338bfa289d424c13f4f438474a"
            "fd71abc18290e0a3c853537a13ce9869d3942c7b6802bfb0f345a9af828b96"
        ),
        gas_limit=2120993272,
        gas_price=10,
        nonce=0,
        value=1548512824,
    )

    post = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
