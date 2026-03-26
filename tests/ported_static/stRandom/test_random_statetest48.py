"""
test_random_statetest48

Ported from:
state_tests/stRandom/randomStatetest48Filler.json
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
    ["state_tests/stRandom/randomStatetest48Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest48(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_random_statetest48"""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xb1f4cbc3a50042184425a6f9e996d0910f7ba879457ce5dac5c71e498ad3c005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    # Source: raw
    # 0x38785231d8e75db11d6da7040cee1a12ebf739e5022caa60f92d51636060b6d96d698fc0e9ced2f6a0087344559c43612f0561a73ba3600a600d6014600963186262c173<contract:target:0x095e7baea6a6c7c4c2dfeb977efac326af552d87>6370f82d9ff1604166f49ef1fea120af77ba4cce3f35bc52ca5c40bf14c77e95ea92e69520143ff9c7827bcfe760aee06d241e31a0773476da22f7ce8131475838c23b59f7a3c46b2b99c0955e169ee3527ca9f7674467bdf2c0eebf6f60129232
    target = pre.deploy_contract(
        code=Op.CODESIZE
        + Op.LOG3(offset=0xa73b, size=0x2f05, topic_1=0x698fc0e9ced2f6a0087344559c43, topic_2=0x6060b6d9, topic_3=0x5231d8e75db11d6da7040cee1a12ebf739e5022caa60f92d51)
        + Op.CALL(gas=0x70f82d9f, address=0x292e762689b448debe7899ade7acb27a84a85c44, value=0x186262c1, args_offset=0x9, args_size=0x14, ret_offset=0xd, ret_size=0xa)
        + Op.PUSH1[0x41] + Op.PUSH7[0xf49ef1fea120af]
        + Op.PUSH24[0xba4cce3f35bc52ca5c40bf14c77e95ea92e69520143ff9c7] + Op.DUP3
        + Op.PUSH28[0xcfe760aee06d241e31a0773476da22f7ce8131475838c23b59f7a3c4]
        + Op.PUSH12[0x2b99c0955e169ee3527ca9f7] + Op.PUSH8[0x4467bdf2c0eebf6f]
        + Op.PUSH1[0x12] + Op.SWAP3 + Op.ORIGIN,
        nonce=0,
        address=Address("0x292e762689b448debe7899ade7acb27a84a85c44"),  # noqa: E501
    )
    # Source: raw
    # 0x6000355415600957005b60203560003555
    coinbase = pre.deploy_contract(
        code=Op.JUMPI(pc=0x9, condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))))  # noqa: E501
        + Op.STOP + Op.JUMPDEST
        + Op.SSTORE(key=Op.CALLDATALOAD(offset=0x0), value=Op.CALLDATALOAD(offset=0x20)),  # noqa: E501
        balance=46,
        nonce=0,
        address=Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=bytes.fromhex("76dd12f3185b84dfc71eb93f4df4ca30dcf34446f25793016424a5e33b6a65fb5d64a9394d7ebefb1c15de971a2d2f53377765d50c698d4e26adea05dd2f6a1688f60eb8b172d796a45c6f79596bfb719df5a571ce8c339e9d7e9b3905324643a2b9fd541956552fc258e688303ecb25082776fde7334cdf046f70c8669a6a05c36909038278e925f0156be9ddb9b83786de8a325ab28e61d18397714bcda0fd5ca879c870d383721c638733b1f78074cc1079e72e0bbbad262348a8976eaaf313a261dccb69dbaf283beebcac7ac3b8166a4deb1fe5099a1c7f3ef595357e76ca260a703bec4848a3cc9804d6de6e5b853b54dd65979292f596ee132edf67eb948e4e4d22f9cb7629bf8b642cb921b2ed9b13e47cb06d6c6f4384c7b372ee7cb61f76a363f8fa68309e3d308179ad3e15fd752d6586e9030c8c1f274878bf7fbe1b569944fdda166c47411878f3702bbe1bbabbce8b10701076e0338bfa289d424c13f4f438474afd71abc18290e0a3c853537a13ce9869d3942c7b6802bfb0f345a9af828b96"),  # noqa: E501
        gas_limit=2120993272,
        value=0x5c4c6e38,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={}, nonce=0),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, code=b"", nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
