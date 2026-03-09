"""
God knows what is happening in this test.

Ported from:
tests/static/state_tests/stSystemOperationsTest/extcodecopyFiller.json
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
    ["tests/static/state_tests/stSystemOperationsTest/extcodecopyFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_extcodecopy(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """God knows what is happening in this test."""
    coinbase = Address("0x4401fcaf7d64d53fb1cfc5c9045c32aa919a8c82")
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

    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.PUSH32[
                0x15688566A82F5F946C68028BF626B349E495DAA43E33529A76437AC416CD1B7D  # noqa: E501
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
            + Op.MLOAD
        ),
        balance=0x5C81EB0,
        nonce=254,
        address=Address("0x0614253558ab9d138504425f7c247229db2c5baf"),  # noqa: E501
    )
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.GAS
            + Op.PUSH1[0x10]
            + Op.PUSH1[0x17]
            + Op.PUSH1[0x11]
            + Op.PUSH1[0x11]
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
            + Op.PUSH27[
                0x58F20FD882EB51408A52E569CE80E93270AB53AE9DE3FEC5498A5C
            ]
            + Op.PUSH19[0xCE1FCD11BB1553736959DF779A616B738C1F40]
            + Op.PUSH29[
                0x12459490AFE302DA311A673488D09E71041D0761DEE4829E3C38E0B1B1
            ]
            + Op.PUSH25[0x7810F2E11E2289983C1AB47CF5EBD38C12F1719232B5F3A7B2]
            + Op.PUSH27[
                0x9EA8858A071C4169392EC725646311235CBD9534E5D7CD8CB5E228
            ]
            + Op.PUSH24[0x38A43F803384F4E62FE6629EA2E609A71759EDAB5C3A58B8]
            + Op.PUSH31[
                0x94C95F710AA6059B0663C9F374CE6EA0A000C5D594C41252D4A74D64896A98  # noqa: E501
            ]
            + Op.PUSH29[
                0xC57C24DF2CE8FFB85ADCC27DCE2D19F7006FBC1C5A7B79A319418FD6C2
            ]
            + Op.PUSH30[
                0xDEBCF170192262D82C1053333F6115C8B258B81E2E84D723C98DBD4535DE
            ]
            + Op.PUSH32[
                0x922723A15827BBCFD07F9E2C5027C7736ED68C61B332059D7EC1BAE1C1FD41A3  # noqa: E501
            ]
            + Op.PUSH2[0xD35B]
            + Op.SWAP10
            + Op.ADDMOD(
                0x4EB39E7FD5076A831D8EB4A3546288A3E1A0,
                0x28C014846148CE67EAF2B33D90672366DAFEAAE0,
                0x9740A588B6ABF3293236AFB92771,
            )
            + Op.PUSH27[
                0xEBE80B6BBFA4041330B05D094A697236FE7654D8A7CE630F83A832
            ]
            + Op.PUSH3[0x125D7]
            + Op.DUP2
            + Op.BALANCE(address=0x6E898F7FDCFD00)
        ),
        balance=0x4D6769F8,
        nonce=221,
        address=Address("0x5b400827141a956ceb3e889ad3e1707aee1a575c"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x4F6CA7B90CEB5FD4)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=bytes.fromhex(
            "6e27b0577f2549e5fa01e3db96e7b03a62e489115538620295677faf15040c1c1796bad1"  # noqa: E501
            "30e2462a8b8d6bbe0fa35bf12087047ef4ff4e66df8772196b4401998ff7f4219c013a0d"  # noqa: E501
            "927b22d8d3fdf625809abb182507d180e687b666f4f1e4f3b8172e87760f436c701264b8"  # noqa: E501
            "9739f3d7c50ec524f16b1a4f91397b760a5209b9b7710544694ecf2729643b3ca545c7"  # noqa: E501
        ),
        gas_limit=100000,
        gas_price=483694712,
        value=614700887,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
