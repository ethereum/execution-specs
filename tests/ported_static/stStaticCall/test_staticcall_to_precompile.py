"""
STATICCALL every precompile from a transaction, a called contract and
initialization code.

Ported from:
state_tests/stStaticCall/StaticcallToPrecompileFromTransactionFiller.yml
state_tests/stStaticCall/StaticcallToPrecompileFromCalledContractFiller.yml
state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml

@manually-enhanced: Do not overwrite. Merged; signer is a constant.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    StateTestFiller,
    Transaction,
    compute_create2_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

SIGNER = Address(0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
CREATE2_SALT = 0x5A175A175A17

PRECOMPILE_CHECKS = (
    Op.MSTORE(
        offset=0x0,
        value=0x18C547E4F7B0F325AD1E56F57E26C745B09A3E503D86E00E5255FF7F715D3D1C,  # noqa: E501
    )
    + Op.MSTORE(offset=0x20, value=0x1C)
    + Op.MSTORE(
        offset=0x40,
        value=0x73B1693892219D736CABA55BDB67216E485557EA6B6AF75F37096C9AA6A5A75F,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x60,
        value=0xEEB940B1D03B21E36B0E47E79769F095FE2AB855BD91E3A38756B7D75A9C4549,  # noqa: E501
    )
    + Op.SSTORE(
        key=0x0,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x1,
            args_offset=0x0,
            args_size=0x80,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(
        key=0x1, value=Op.MOD(Op.MLOAD(offset=0x3E8), Op.EXP(0x2, 0xA0))
    )
    + Op.SSTORE(key=0x2, value=Op.EQ(SIGNER, Op.SLOAD(key=0x1)))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x20, value=0x0)
    + Op.MSTORE(offset=0x40, value=0x0)
    + Op.MSTORE(offset=0x60, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
    )
    + Op.SSTORE(
        key=0x3,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x2,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(key=0x4, value=Op.MLOAD(offset=0x0))
    + Op.SSTORE(key=0x5, value=Op.MLOAD(offset=0x3E8))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
    )
    + Op.SSTORE(
        key=0x6,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x3,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(key=0x7, value=Op.MLOAD(offset=0x0))
    + Op.SSTORE(key=0x8, value=Op.MLOAD(offset=0x3E8))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
    )
    + Op.SSTORE(
        key=0x9,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x4,
            args_offset=0x0,
            args_size=0x20,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(key=0x10, value=Op.MLOAD(offset=0x3E8))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(offset=0x0, value=0x1)
    + Op.MSTORE(offset=0x20, value=0x20)
    + Op.MSTORE(offset=0x40, value=0x20)
    + Op.MSTORE(
        offset=0x60,
        value=0x3FFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x80,
        value=0x2EFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0xA0,
        value=0x2F00000000000000000000000000000000000000000000000000000000000000,  # noqa: E501
    )
    + Op.SSTORE(
        key=0x11,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x5,
            args_offset=0x0,
            args_size=0xA1,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(key=0x12, value=Op.MLOAD(offset=0x3E8))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x20, value=0x0)
    + Op.MSTORE(offset=0x40, value=0x0)
    + Op.MSTORE(offset=0x60, value=0x0)
    + Op.MSTORE(offset=0x80, value=0x0)
    + Op.MSTORE(offset=0xA0, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x20,
        value=0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x40,
        value=0x1DE49A4B0233273BBA8146AF82042D004F2085EC982397DB0D97DA17204CC286,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x60,
        value=0x217327FFC463919BEF80CC166D09C6172639D8589799928761BCD9F22C903D4,  # noqa: E501
    )
    + Op.SSTORE(
        key=0x13,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x6,
            args_offset=0x0,
            args_size=0x80,
            ret_offset=0x3E8,
            ret_size=0x40,
        ),
    )
    + Op.SSTORE(key=0x14, value=Op.MLOAD(offset=0x3E8))
    + Op.SSTORE(key=0x15, value=Op.MLOAD(offset=0x408))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x20, value=0x0)
    + Op.MSTORE(offset=0x40, value=0x0)
    + Op.MSTORE(offset=0x60, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(offset=0x408, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x20,
        value=0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
    )
    + Op.MSTORE(offset=0x40, value=0x3)
    + Op.SSTORE(
        key=0x16,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x7,
            args_offset=0x0,
            args_size=0x60,
            ret_offset=0x3E8,
            ret_size=0x40,
        ),
    )
    + Op.SSTORE(key=0x17, value=Op.MLOAD(offset=0x3E8))
    + Op.SSTORE(key=0x18, value=Op.MLOAD(offset=0x408))
    + Op.MSTORE(offset=0x0, value=0x0)
    + Op.MSTORE(offset=0x20, value=0x0)
    + Op.MSTORE(offset=0x40, value=0x0)
    + Op.MSTORE(offset=0x3E8, value=0x0)
    + Op.MSTORE(offset=0x408, value=0x0)
    + Op.MSTORE(
        offset=0x0,
        value=0x1C76476F4DEF4BB94541D57EBBA1193381FFA7AA76ADA664DD31C16024C43F59,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x20,
        value=0x3034DD2920F673E204FEE2811C678745FC819B55D3E9D294E45C9B03A76AEF41,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x40,
        value=0x209DD15EBFF5D46C4BD888E51A93CF99A7329636C63514396B4A452003A35BF7,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x60,
        value=0x4BF11CA01483BFA8B34B43561848D28905960114C8AC04049AF4B6315A41678,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x80,
        value=0x2BB8324AF6CFC93537A2AD1A445CFD0CA2A71ACD7AC41FADBF933C2A51BE344D,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0xA0,
        value=0x120A2A4CF30C1BF9845F20C6FE39E07EA2CCE61F0C9BB048165FE5E4DE877550,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0xC0,
        value=0x111E129F1CF1097710D41C4AC70FCDFA5BA2023C6FF1CBEAC322DE49D1B6DF7C,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0xE0,
        value=0x2032C61A830E3C17286DE9462BF242FCA2883585B93870A73853FACE6A6BF411,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x100,
        value=0x198E9393920D483A7260BFB731FB5D25F1AA493335A9E71297E485B7AEF312C2,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x120,
        value=0x1800DEEF121F1E76426A00665E5C4479674322D4F75EDADD46DEBD5CD992F6ED,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x140,
        value=0x90689D0585FF075EC9E99AD690C3395BC4B313370B38EF355ACDADCD122975B,  # noqa: E501
    )
    + Op.MSTORE(
        offset=0x160,
        value=0x12C85EA5DB8C6DEB4AAB71808DCB408FE3D1E7690C43D37B4CE6CC0166FA7DAA,  # noqa: E501
    )
    + Op.SSTORE(
        key=0x19,
        value=Op.STATICCALL(
            gas=Op.GAS,
            address=0x8,
            args_offset=0x0,
            args_size=0x180,
            ret_offset=0x3E8,
            ret_size=0x20,
        ),
    )
    + Op.SSTORE(key=0x20, value=Op.MLOAD(offset=0x3E8))
    + Op.STOP
)

EXPECTED_STORAGE = {
    0: 1,
    1: SIGNER,
    2: 1,
    3: 1,
    4: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
    5: 0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
    6: 1,
    7: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
    8: 0x14EF238CFA4075E9EDE92F18B1566C1DD0B99AAA,
    9: 1,
    16: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
    17: 1,
    18: 1,
    19: 1,
    20: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
    21: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
    22: 1,
    23: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
    24: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
    25: 1,
    32: 1,
}


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/StaticcallToPrecompileFromTransactionFiller.yml",  # noqa: E501
        "state_tests/stStaticCall/StaticcallToPrecompileFromCalledContractFiller.yml",  # noqa: E501
        "state_tests/stStaticCall/StaticcallToPrecompileFromContractInitializationFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "context",
    ["transaction", "called_contract", "contract_initialization"],
)
def test_staticcall_to_precompile(
    state_test: StateTestFiller,
    pre: Alloc,
    context: str,
) -> None:
    """Verify STATICCALL to each precompile succeeds in every context."""
    sender = pre.fund_eoa()
    post: dict = {}
    if context == "transaction":
        checker = pre.deploy_contract(code=PRECOMPILE_CHECKS)
        tx = Transaction(sender=sender, to=checker)
    elif context == "called_contract":
        checker = pre.deploy_contract(code=PRECOMPILE_CHECKS)
        caller = pre.deploy_contract(
            code=Op.SSTORE(0, Op.CALL(address=checker)) + Op.STOP
        )
        tx = Transaction(sender=sender, to=caller)
        post[caller] = Account(storage={0: 1})
    elif context == "contract_initialization":
        factory = pre.deploy_contract(
            code=Op.CALLDATACOPY(size=Op.CALLDATASIZE)
            + Op.SSTORE(
                0,
                Op.CREATE2(size=Op.CALLDATASIZE, salt=CREATE2_SALT),
            )
            + Op.STOP
        )
        checker = compute_create2_address(
            address=factory, salt=CREATE2_SALT, initcode=PRECOMPILE_CHECKS
        )
        tx = Transaction(sender=sender, to=factory, data=PRECOMPILE_CHECKS)
        post[factory] = Account(storage={0: checker})
    else:
        raise ValueError(f"Unknown context: {context}")
    post[checker] = Account(storage=EXPECTED_STORAGE)

    state_test(pre=pre, post=post, tx=tx)
