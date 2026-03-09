"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stRandom2/randomStatetest639Filler.json
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
    ["tests/static/state_tests/stRandom2/randomStatetest639Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
def test_random_statetest639(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x4f3f701464972e74606d6ea82d4d3080599a0e79")
    sender = EOA(
        key=0xB1F4CBC3A50042184425A6F9E996D0910F7BA879457CE5DAC5C71E498AD3C005
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=9223372036854775807,
    )

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: raw bytecode
    pre.deploy_contract(
        code=(
            Op.JUMPI(
                pc=0x9,
                condition=Op.ISZERO(Op.SLOAD(key=Op.CALLDATALOAD(offset=0x0))),
            )
            + Op.STOP
            + Op.JUMPDEST
            + Op.SSTORE(
                key=Op.CALLDATALOAD(offset=0x0),
                value=Op.CALLDATALOAD(offset=0x20),
            )
        ),
        balance=46,
        nonce=0,
        address=coinbase,  # noqa: E501
    )
    # Source: raw bytecode
    contract = pre.deploy_contract(
        code=(
            Op.SGT(
                0xAB95E6F8772A548229700E2DCC612AC9CEEB898AF8436680A2E1074DF8CED0,  # noqa: E501
                0x993D78E80807A0D34BDBFA4E0AFA9D,
            )
            + Op.LOG1(
                offset=0xB1F5,
                size=0xC1,
                topic_1=0x64D71C8FE8A10FB58F8706EA3EE1B54A0848E742CA357E3D0234,
            )
            + Op.ISZERO(
                0x48DA2AE1E6987C52223414746FAB0E39130693D15A48D39B5130096A7C,
            )
            + Op.PUSH17[0xC4FB89343EF5D10E912DECBA682BF205DE]
            + Op.PUSH26[0xE84C573C9E2B0FFBD4D6117E40046B4C2D77156ADA28960D9BB9]
            + Op.PUSH32[
                0x56D243429AA245C32E1F800A686EBE298DD08349D864486D7A1569B5AAE49577  # noqa: E501
            ]
            + Op.PUSH12[0xB5E71206CD09F54D1CD71396]
            + Op.PUSH6[0x57567542184C]
            + Op.PUSH21[0xB95CC0D8AC3D0E05D0264B8D42A3563826123FC0D9]
            + Op.PUSH5[0x521B61B863]
            + Op.PUSH21[0x591A821818672EF0DEA05D259BC4F98C34418D9E7A]
            + Op.PUSH8[0x7173B211649C07DF]
            + Op.PUSH23[0x70ACA688053842DE6157C4FB5E678ADC0611FCC20A1D83]
            + Op.PUSH15[0xC69B9370D09B83F1B0293A1B102D6D]
            + Op.PUSH20[0x978584B14FB2AB517001867E6545DD2DC3438F9C]
            + Op.PUSH25[0x28F6D3C6E4DA98113CE2486C1AD028DC9947B28590071B977E]
            + Op.PUSH6[0x1D352B078CB9]
            + Op.PUSH12[0x27F9FF7252C9F3CE9E5151AE]
            + Op.PUSH27[
                0xF1064AB8A5D92ED543B9D59C341F85BB22AA2FA7D7EE7310AC8F51
            ]
            + Op.SWAP15
            + Op.PUSH7[0xDA165B9EFE3663]
            + Op.PUSH6[0x7B1E28F4EB3E]
            + Op.PUSH20[0x38391339AF5346D12C14BBC0863C26D7E999776C]
            + Op.PUSH26[0x39CEFAC542ED69F518BBEF5461C0DF385004F5411C3FAAA65C7B]
            + Op.PUSH11[0xBF900CA1EF1F40BB938F72]
            + Op.PUSH23[0x95A1CA14012BA07CC01548F3DF75544B11BB52B7693BED]
            + Op.PUSH31[
                0x2FC1537B2F8D63C4DB4C3D8FC72B6F5F7E7B4D1EC8C1AC89230936975D1962  # noqa: E501
            ]
            + Op.PUSH8[0x88F03504A8C9ACF6]
            + Op.PUSH5[0x37D6D88560]
            + Op.PUSH24[0x78BEE6FE54742DDC9A7D8373DBFE2E21AACF8816944C02EF]
            + Op.SWAP9
            + Op.ORIGIN
            + Op.CALL(
                gas=0x56837182,
                address=0x9FECB32D9AE49C08DA1E2551BA9257BE9A181E76,
                value=0x29EC801E,
                args_offset=0x18,
                args_size=0x9,
                ret_offset=0x9,
                ret_size=0x15,
            )
            + Op.PUSH22[0x259FC2EA2DF7D720FB0914ED44BCB12B8FF15E712EF6]
            + Op.PUSH30[
                0x868FE7FBA6B46FAC671A45BCACE82FA83B87B8744835AC63D2B6CF3D157D
            ]
            + Op.PUSH22[0x26909F9C4D1EFBF68D780AF1C0F2DABBFC53D2C71DC4]
            + Op.PUSH2[0xBF7F]
            + Op.PUSH25[0x8E3A9C48CD1DF8D146A7DF97125985162ECD37B059204323D0]
            + Op.PUSH7[0xCB4709A3A1715F]
            + Op.PUSH29[
                0x4A9FB905C26BA87933EF2499D3447D5CD4DF27A6205C8A1CE06719C3E0
            ]
            + Op.PUSH6[0xE66AB80222FF]
            + Op.PUSH31[
                0xD1F72F533A1160330DBD8DCD0489EC2DAC84D7522A4D8732C5AE9E08D9A251  # noqa: E501
            ]
            + Op.PUSH9[0x2FB33FA08ECC05197D]
            + Op.DUP10
            + Op.PUSH27[
                0x1D5F28328CAA78CA6CD6B86FD08A1748FA959665861D18C25A3CAE
            ]
            + Op.PUSH26[0x732FE4FB3AD8B48C17C8EFEEB5EC22BE8B20EC4EAE2955D65B9A]
            + Op.PUSH13[0x1415C23047AA8F2C29AEDDD787]
            + Op.PUSH6[0xC1BC3EDA6341]
            + Op.PUSH14[0x84CDB9B8D7942020DB3B1ED861A9]
            + Op.PUSH7[0x475EB6EF9F9920]
            + Op.PUSH10[0x2A879EE6BF9D0A1DD9D3]
            + Op.DUP7
        ),
        nonce=0,
        address=Address("0x9fecb32d9ae49c08da1e2551ba9257be9a181e76"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1612042127,
        value=1237321880,
    )

    post: dict = {}

    state_test(env=env, pre=pre, post=post, tx=tx)
