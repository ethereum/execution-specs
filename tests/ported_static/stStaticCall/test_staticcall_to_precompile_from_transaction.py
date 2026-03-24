"""
STATICCALL to precompiled contracts from transaction code.

It should execute successfully for each precompiled contract.

Ported from:
tests/static/state_tests/stStaticCall
StaticcallToPrecompileFromTransactionFiller.yml
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
    [
        "tests/static/state_tests/stStaticCall/StaticcallToPrecompileFromTransactionFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.valid_until("Prague")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_staticcall_to_precompile_from_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """STATICCALL to precompiled contracts from transaction code."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # {
    #   ;; Recovery of ECDSA signature
    #   [ 0x00 ] 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c  # noqa: E501
    #   [ 0x20 ] 28
    #   [ 0x40 ] 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f  # noqa: E501
    #   [ 0x60 ] 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549  # noqa: E501
    #   [[ 0x00 ]] (STATICCALL (GAS) 1 0 128 1000 32)
    #   [[ 0x01 ]] (MOD @1000 (EXP 2 160))
    #   [[ 0x02 ]] (EQ (ORIGIN) @@1)
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x20 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x40 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x60 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #
    #   ;; Hash function SHA256
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000  # noqa: E501
    #   [[ 0x03 ]] (STATICCALL (GAS) 2 0 32 1000 32)
    #   [[ 0x04 ]] @0
    #   [[ 0x05 ]] @1000
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #
    #   ;; Hash function RIPEMD160
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000  # noqa: E501
    #   [[ 0x06 ]] (STATICCALL (GAS) 3 0 32 1000 32)
    #   [[ 0x07 ]] @0
    #   [[ 0x08 ]] @1000
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    # ... (70 more lines)
    contract = pre.deploy_contract(
        code=(
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
                key=0x1,
                value=Op.MOD(Op.MLOAD(offset=0x3E8), Op.EXP(0x2, 0xA0)),
            )
            + Op.SSTORE(key=0x2, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x1)))
            + Op.MSTORE(offset=0x0, value=0x0)
            + Op.MSTORE(offset=0x20, value=0x0)
            + Op.MSTORE(offset=0x40, value=0x0)
            + Op.MSTORE(offset=0x60, value=0x0)
            + Op.MSTORE(offset=0x3E8, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
        ),
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100,
    )

    post = {
        contract: Account(
            storage={
                0: 1,
                1: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
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
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/StaticcallToPrecompileFromTransactionFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Osaka")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_staticcall_to_precompile_from_transaction_from_osaka(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """STATICCALL to precompiled contracts from transaction code."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # {
    #   ;; Recovery of ECDSA signature
    #   [ 0x00 ] 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c  # noqa: E501
    #   [ 0x20 ] 28
    #   [ 0x40 ] 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f  # noqa: E501
    #   [ 0x60 ] 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549  # noqa: E501
    #   [[ 0x00 ]] (STATICCALL (GAS) 1 0 128 1000 32)
    #   [[ 0x01 ]] (MOD @1000 (EXP 2 160))
    #   [[ 0x02 ]] (EQ (ORIGIN) @@1)
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x20 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x40 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x60 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #
    #   ;; Hash function SHA256
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000  # noqa: E501
    #   [[ 0x03 ]] (STATICCALL (GAS) 2 0 32 1000 32)
    #   [[ 0x04 ]] @0
    #   [[ 0x05 ]] @1000
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #
    #   ;; Hash function RIPEMD160
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000  # noqa: E501
    #   [[ 0x06 ]] (STATICCALL (GAS) 3 0 32 1000 32)
    #   [[ 0x07 ]] @0
    #   [[ 0x08 ]] @1000
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 1000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    # ... (70 more lines)
    contract = pre.deploy_contract(
        code=(
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
                key=0x1,
                value=Op.MOD(Op.MLOAD(offset=0x3E8), Op.EXP(0x2, 0xA0)),
            )
            + Op.SSTORE(key=0x2, value=Op.EQ(Op.ORIGIN, Op.SLOAD(key=0x1)))
            + Op.MSTORE(offset=0x0, value=0x0)
            + Op.MSTORE(offset=0x20, value=0x0)
            + Op.MSTORE(offset=0x40, value=0x0)
            + Op.MSTORE(offset=0x60, value=0x0)
            + Op.MSTORE(offset=0x3E8, value=0x0)
            + Op.MSTORE(
                offset=0x0,
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
                value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
        ),
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100,
    )

    post = {
        contract: Account(
            storage={
                0: 1,
                1: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
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
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
