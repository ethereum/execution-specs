"""
God knows what is happening in this test.

Ported from:
state_tests/stSystemOperationsTest/extcodecopyFiller.json
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Fork,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Amsterdam
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stSystemOperationsTest/extcodecopyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodecopy(
    state_test: StateTestFiller,
    fork: Fork,
    pre: Alloc,
) -> None:
    """God knows what is happening in this test."""
    coinbase = Address(0x4401FCAF7D64D53FB1CFC5C9045C32AA919A8C82)
    sender = EOA(
        key=0x7446B5F5F4C3994BA600DA46B6CA0E5DBD71BCE76740B040BA716507ECB75BB9
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=1478962728,
    )

    # Source: raw
    # 0x7f15688566a82f5f946c68028bf626b349e495daa43e33529a76437ac416cd1b7d6e7dae7454bb193b1c28e64a6a935bc373cea0c5cc171fa61277e5604a3bc8aef4de3d38820658600b80797ada6e82e95f6520383f95f5c7dae56b4dc13b6f22ecabfce07c3cff51  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH32[
            0x15688566A82F5F946C68028BF626B349E495DAA43E33529A76437AC416CD1B7D
        ]
        + Op.MOD(
            0xCEA0C5CC171FA61277E5604A3BC8AEF4DE3D3882,
            0x7DAE7454BB193B1C28E64A6A935BC3,
        )
        + Op.EXTCODECOPY(
            address=0x7ADA6E82E95F6520383F95F5C7DAE56B4DC13B6F22ECABFCE07C,
            dest_offset=Op.DUP1,
            offset=0xB,
            size=Op.PC,
        )
        + Op.SELFDESTRUCT
        + Op.MLOAD,
        balance=0x5C81EB0,
        nonce=254,
        address=Address(0x0614253558AB9D138504425F7C247229DB2C5BAF),  # noqa: E501
    )
    # Source: raw
    # 0x5a60106017601160116018601c600f601b601d5f60026013600f601a8d5a5b7679177b5dd41a23db52998c4dcd14e88390dcc9f3ed5783601660145f6013600d601f60016011600e600c600d601f60138c7a58f20fd882eb51408a52e569ce80e93270ab53ae9de3fec5498a5c72ce1fcd11bb1553736959df779a616b738c1f407c12459490afe302da311a673488d09e71041d0761dee4829e3c38e0b1b1787810f2e11e2289983c1ab47cf5ebd38c12f1719232b5f3a7b27a9ea8858a071c4169392ec725646311235cbd9534e5d7cd8cb5e2287738a43f803384f4e62fe6629ea2e609a71759edab5c3a58b87e94c95f710aa6059b0663c9f374ce6ea0a000c5d594c41252d4a74d64896a987cc57c24df2ce8ffb85adcc27dce2d19f7006fbc1c5a7b79a319418fd6c27ddebcf170192262d82c1053333f6115c8b258b81e2e84d723c98dbd4535de7f922723a15827bbcfd07f9e2c5027c7736ed68c61b332059d7ec1bae1c1fd41a361d35b996d9740a588b6abf3293236afb927717328c014846148ce67eaf2b33d90672366dafeaae0714eb39e7fd5076a831d8eb4a3546288a3e1a0087aebe80b6bbfa4041330b05d094a697236fe7654d8a7ce630f83a832620125d781666e898f7fdcfd0031  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.GAS
        + Op.PUSH1[0x10]
        + Op.PUSH1[0x17]
        + Op.PUSH1[0x11] * 2
        + Op.PUSH1[0x18]
        + Op.PUSH1[0x1C]
        + Op.PUSH1[0xF]
        + Op.PUSH1[0x1B]
        + Op.PUSH1[0x1D]
        + Op.PUSH0
        + Op.PUSH1[0x2]
        + Op.PUSH1[0x13]
        + Op.PUSH1[0xF]
        + Op.PUSH1[0x1A]
        + Op.DUP14
        + Op.GAS
        + Op.JUMPDEST
        + Op.PUSH23[0x79177B5DD41A23DB52998C4DCD14E88390DCC9F3ED5783]
        + Op.PUSH1[0x16]
        + Op.PUSH1[0x14]
        + Op.PUSH0
        + Op.PUSH1[0x13]
        + Op.PUSH1[0xD]
        + Op.PUSH1[0x1F]
        + Op.PUSH1[0x1]
        + Op.PUSH1[0x11]
        + Op.PUSH1[0xE]
        + Op.PUSH1[0xC]
        + Op.PUSH1[0xD]
        + Op.PUSH1[0x1F]
        + Op.PUSH1[0x13]
        + Op.DUP13
        + Op.PUSH27[0x58F20FD882EB51408A52E569CE80E93270AB53AE9DE3FEC5498A5C]
        + Op.PUSH19[0xCE1FCD11BB1553736959DF779A616B738C1F40]
        + Op.PUSH29[
            0x12459490AFE302DA311A673488D09E71041D0761DEE4829E3C38E0B1B1
        ]
        + Op.PUSH25[0x7810F2E11E2289983C1AB47CF5EBD38C12F1719232B5F3A7B2]
        + Op.PUSH27[0x9EA8858A071C4169392EC725646311235CBD9534E5D7CD8CB5E228]
        + Op.PUSH24[0x38A43F803384F4E62FE6629EA2E609A71759EDAB5C3A58B8]
        + Op.PUSH31[
            0x94C95F710AA6059B0663C9F374CE6EA0A000C5D594C41252D4A74D64896A98
        ]
        + Op.PUSH29[
            0xC57C24DF2CE8FFB85ADCC27DCE2D19F7006FBC1C5A7B79A319418FD6C2
        ]
        + Op.PUSH30[
            0xDEBCF170192262D82C1053333F6115C8B258B81E2E84D723C98DBD4535DE
        ]
        + Op.PUSH32[
            0x922723A15827BBCFD07F9E2C5027C7736ED68C61B332059D7EC1BAE1C1FD41A3
        ]
        + Op.PUSH2[0xD35B]
        + Op.SWAP10
        + Op.ADDMOD(
            0x4EB39E7FD5076A831D8EB4A3546288A3E1A0,
            0x28C014846148CE67EAF2B33D90672366DAFEAAE0,
            0x9740A588B6ABF3293236AFB92771,
        )
        + Op.PUSH27[0xEBE80B6BBFA4041330B05D094A697236FE7654D8A7CE630F83A832]
        + Op.PUSH3[0x125D7]
        + Op.DUP2
        + Op.BALANCE(address=0x6E898F7FDCFD00),
        balance=0x4D6769F8,
        nonce=221,
        address=Address(0x5B400827141A956CEB3E889AD3E1707AEE1A575C),  # noqa: E501
    )
    pre[sender] = Account(balance=0x4F6CA7B90CEB5FD4)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(
            "6e27b0577f2549e5fa01e3db96e7b03a62e489115538620295677faf15040c1c1796bad130e2462a8b8d6bbe0fa35bf12087047ef4ff4e66df8772196b4401998ff7f4219c013a0d927b22d8d3fdf625809abb182507d180e687b666f4f1e4f3b8172e87760f436c701264b89739f3d7c50ec524f16b1a4f91397b760a5209b9b7710544694ecf2729643b3ca545c7"  # noqa: E501
        ),
        gas_limit=2100000 if fork >= Amsterdam else 100000,
        value=0x24A39757,
        gas_price=483694712,
    )

    post = {
        Address(0x00000000002147C39FD6B5C19B7B89FC003E6B16): Account(
            storage={}, nonce=0
        ),
        coinbase: Account(storage={}, nonce=0),
        sender: Account(storage={}, nonce=1),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
