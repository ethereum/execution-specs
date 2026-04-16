"""
Contract B staticcalls contract A.

Contract A callcodes precompiled contracts.
It should execute successfully for each precompiled contract.


Ported from:
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromTransactionFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_to_precompile_from_transaction(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Contract B staticcalls contract A."""
    coinbase = Address(0xCAFE000000000000000000000000000000000001)
    contract_0 = Address(0xB000000000000000000000000000000000000000)
    contract_1 = Address(0xA000000000000000000000000000000000000000)
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

    pre[sender] = Account(balance=0xDE0B6B3A7640000)
    # Source: lll
    # {
    #   ;; Recovery of ECDSA signature
    #   [ 0x00 ] 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c  # noqa: E501
    #   [ 0x20 ] 28
    #   [ 0x40 ] 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f  # noqa: E501
    #   [ 0x60 ] 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549  # noqa: E501
    #   ;; zero value
    #   [ 0x0a0000 ] (CALLCODE (GAS) 1 0 0 128 0x2000 32)
    #   [ 0x0a0100 ] (MOD @0x2000 (EXP 2 160))
    #   [ 0x0a0200 ] (EQ (ORIGIN) @0x0a0100)
    #   [ 0x2000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   ;; non zero value
    #   [ 0x0b0000 ] (CALLCODE (GAS) 1 1 0 128 0x2020 32)
    #   [ 0x0b0100 ] (MOD @0x2020 (EXP 2 160))
    #   [ 0x0b0200 ] (EQ (ORIGIN) @0x0b0100)
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x20 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x40 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x60 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   [ 0x2020 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #
    #   ;; Hash function SHA256
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000  # noqa: E501
    #   ;; zero value
    #   [ 0x0a0300 ] (CALLCODE (GAS) 2 0 0 32 0x2000 32)
    #   [ 0x0a0400 ] @0
    #   [ 0x0a0500 ] @0x2000
    #   [ 0x2000 ] 0x0000000000000000000000000000000000000000000000000000000000000000  # noqa: E501
    #   ;; non zero value
    #   [ 0x0b0300 ] (CALLCODE (GAS) 2 1 0 32 0x2020 32)
    # ... (121 more lines)
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(
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
        + Op.MSTORE(
            offset=0xA0000,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x1,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(
            offset=0xA0100,
            value=Op.MOD(Op.MLOAD(offset=0x2000), Op.EXP(0x2, 0xA0)),
        )
        + Op.MSTORE(
            offset=0xA0200, value=Op.EQ(Op.ORIGIN, Op.MLOAD(offset=0xA0100))
        )
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB0000,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x1,
                value=0x1,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(
            offset=0xB0100,
            value=Op.MOD(Op.MLOAD(offset=0x2020), Op.EXP(0x2, 0xA0)),
        )
        + Op.MSTORE(
            offset=0xB0200, value=Op.EQ(Op.ORIGIN, Op.MLOAD(offset=0xB0100))
        )
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
        )
        + Op.MSTORE(
            offset=0xA0300,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x2,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xA0400, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xA0500, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB0300,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x2,
                value=0x1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xB0400, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xB0500, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
        )
        + Op.MSTORE(
            offset=0xA0600,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x3,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xA0700, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xA0800, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB0600,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x3,
                value=0x1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xB0700, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xB0800, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,
        )
        + Op.MSTORE(
            offset=0xA0900,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x4,
                value=0x0,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xA1000, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB0900,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x4,
                value=0x1,
                args_offset=0x0,
                args_size=0x20,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xB1000, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
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
        + Op.MSTORE(
            offset=0xA1100,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x5,
                value=0x0,
                args_offset=0x0,
                args_size=0xA1,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xA1200, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB1100,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x5,
                value=0x1,
                args_offset=0x0,
                args_size=0xA1,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xB1200, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x80, value=0x0)
        + Op.MSTORE(offset=0xA0, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
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
        + Op.MSTORE(
            offset=0xA1300,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x6,
                value=0x0,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x2000,
                ret_size=0x40,
            ),
        )
        + Op.MSTORE(offset=0xA1400, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0xA1500, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(
            offset=0xB1300,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x6,
                value=0x1,
                args_offset=0x0,
                args_size=0x80,
                ret_offset=0x3000,
                ret_size=0x40,
            ),
        )
        + Op.MSTORE(offset=0xB1400, value=Op.MLOAD(offset=0x3000))
        + Op.MSTORE(offset=0xB1500, value=Op.MLOAD(offset=0x3020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x3000, value=0x0)
        + Op.MSTORE(offset=0x3020, value=0x0)
        + Op.MSTORE(
            offset=0x0,
            value=0xF25929BCB43D5A57391564615C9E70A992B10EAFA4DB109709649CF48C50DD2,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x16DA2F5CB6BE7A0AA72C440C53C9BBDFEC6C36C7D515536431B3A865468ACBBA,  # noqa: E501
        )
        + Op.MSTORE(offset=0x40, value=0x3)
        + Op.MSTORE(
            offset=0xA1600,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x7,
                value=0x0,
                args_offset=0x0,
                args_size=0x60,
                ret_offset=0x2000,
                ret_size=0x40,
            ),
        )
        + Op.MSTORE(offset=0xA1700, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0xA1800, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(
            offset=0xB1600,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x7,
                value=0x1,
                args_offset=0x0,
                args_size=0x60,
                ret_offset=0x3000,
                ret_size=0x40,
            ),
        )
        + Op.MSTORE(offset=0xB1700, value=Op.MLOAD(offset=0x3000))
        + Op.MSTORE(offset=0xB1800, value=Op.MLOAD(offset=0x3020))
        + Op.MSTORE(offset=0x0, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0)
        + Op.MSTORE(offset=0x3000, value=0x0)
        + Op.MSTORE(offset=0x3020, value=0x0)
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
        + Op.MSTORE(
            offset=0xA1900,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x8,
                value=0x0,
                args_offset=0x0,
                args_size=0x180,
                ret_offset=0x2000,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xA2000, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(
            offset=0xB1900,
            value=Op.CALLCODE(
                gas=Op.GAS,
                address=0x8,
                value=0x1,
                args_offset=0x0,
                args_size=0x180,
                ret_offset=0x2020,
                ret_size=0x20,
            ),
        )
        + Op.MSTORE(offset=0xB2000, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.RETURN(offset=0xA0000, size=0x12020)
        + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address(0xA000000000000000000000000000000000000000),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0x00 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed  # noqa: E501
    #   (STATICCALL (GAS) 0xa000000000000000000000000000000000000000 0 0 0x0a0000 0x012020)  # noqa: E501
    #   [[ 0x01 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed  # noqa: E501
    #   ;; save results to store
    #   [[ 0x0a00 ]] @0x0a0000  [[ 0x0b00 ]] @0x0b0000
    #   [[ 0x0a01 ]] @0x0a0100  [[ 0x0b01 ]] @0x0b0100
    #   [[ 0x0a02 ]] @0x0a0200  [[ 0x0b02 ]] @0x0b0200
    #   [[ 0x0a03 ]] @0x0a0300  [[ 0x0b03 ]] @0x0b0300
    #   [[ 0x0a04 ]] @0x0a0400  [[ 0x0b04 ]] @0x0b0400
    #   [[ 0x0a05 ]] @0x0a0500  [[ 0x0b05 ]] @0x0b0500
    #   [[ 0x0a06 ]] @0x0a0600  [[ 0x0b06 ]] @0x0b0600
    #   [[ 0x0a07 ]] @0x0a0700  [[ 0x0b07 ]] @0x0b0700
    #   [[ 0x0a08 ]] @0x0a0800  [[ 0x0b08 ]] @0x0b0800
    #   [[ 0x0a09 ]] @0x0a0900  [[ 0x0b09 ]] @0x0b0900
    #   [[ 0x0a10 ]] @0x0a1000  [[ 0x0b10 ]] @0x0b1000
    #   [[ 0x0a11 ]] @0x0a1100  [[ 0x0b11 ]] @0x0b1100
    #   [[ 0x0a12 ]] @0x0a1200  [[ 0x0b12 ]] @0x0b1200
    #   [[ 0x0a13 ]] @0x0a1300  [[ 0x0b13 ]] @0x0b1300
    #   [[ 0x0a14 ]] @0x0a1400  [[ 0x0b14 ]] @0x0b1400
    #   [[ 0x0a15 ]] @0x0a1500  [[ 0x0b15 ]] @0x0b1500
    #   [[ 0x0a16 ]] @0x0a1600  [[ 0x0b16 ]] @0x0b1600
    #   [[ 0x0a17 ]] @0x0a1700  [[ 0x0b17 ]] @0x0b1700
    #   [[ 0x0a18 ]] @0x0a1800  [[ 0x0b18 ]] @0x0b1800
    #   [[ 0x0a19 ]] @0x0a1900  [[ 0x0b19 ]] @0x0b1900
    #   [[ 0x0a20 ]] @0x0a2000  [[ 0x0b20 ]] @0x0b2000
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED,  # noqa: E501
        )
        + Op.POP(
            Op.STATICCALL(
                gas=Op.GAS,
                address=contract_1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0xA0000,
                ret_size=0x12020,
            )
        )
        + Op.SSTORE(
            key=0x1,
            value=0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED,  # noqa: E501
        )
        + Op.SSTORE(key=0xA00, value=Op.MLOAD(offset=0xA0000))
        + Op.SSTORE(key=0xB00, value=Op.MLOAD(offset=0xB0000))
        + Op.SSTORE(key=0xA01, value=Op.MLOAD(offset=0xA0100))
        + Op.SSTORE(key=0xB01, value=Op.MLOAD(offset=0xB0100))
        + Op.SSTORE(key=0xA02, value=Op.MLOAD(offset=0xA0200))
        + Op.SSTORE(key=0xB02, value=Op.MLOAD(offset=0xB0200))
        + Op.SSTORE(key=0xA03, value=Op.MLOAD(offset=0xA0300))
        + Op.SSTORE(key=0xB03, value=Op.MLOAD(offset=0xB0300))
        + Op.SSTORE(key=0xA04, value=Op.MLOAD(offset=0xA0400))
        + Op.SSTORE(key=0xB04, value=Op.MLOAD(offset=0xB0400))
        + Op.SSTORE(key=0xA05, value=Op.MLOAD(offset=0xA0500))
        + Op.SSTORE(key=0xB05, value=Op.MLOAD(offset=0xB0500))
        + Op.SSTORE(key=0xA06, value=Op.MLOAD(offset=0xA0600))
        + Op.SSTORE(key=0xB06, value=Op.MLOAD(offset=0xB0600))
        + Op.SSTORE(key=0xA07, value=Op.MLOAD(offset=0xA0700))
        + Op.SSTORE(key=0xB07, value=Op.MLOAD(offset=0xB0700))
        + Op.SSTORE(key=0xA08, value=Op.MLOAD(offset=0xA0800))
        + Op.SSTORE(key=0xB08, value=Op.MLOAD(offset=0xB0800))
        + Op.SSTORE(key=0xA09, value=Op.MLOAD(offset=0xA0900))
        + Op.SSTORE(key=0xB09, value=Op.MLOAD(offset=0xB0900))
        + Op.SSTORE(key=0xA10, value=Op.MLOAD(offset=0xA1000))
        + Op.SSTORE(key=0xB10, value=Op.MLOAD(offset=0xB1000))
        + Op.SSTORE(key=0xA11, value=Op.MLOAD(offset=0xA1100))
        + Op.SSTORE(key=0xB11, value=Op.MLOAD(offset=0xB1100))
        + Op.SSTORE(key=0xA12, value=Op.MLOAD(offset=0xA1200))
        + Op.SSTORE(key=0xB12, value=Op.MLOAD(offset=0xB1200))
        + Op.SSTORE(key=0xA13, value=Op.MLOAD(offset=0xA1300))
        + Op.SSTORE(key=0xB13, value=Op.MLOAD(offset=0xB1300))
        + Op.SSTORE(key=0xA14, value=Op.MLOAD(offset=0xA1400))
        + Op.SSTORE(key=0xB14, value=Op.MLOAD(offset=0xB1400))
        + Op.SSTORE(key=0xA15, value=Op.MLOAD(offset=0xA1500))
        + Op.SSTORE(key=0xB15, value=Op.MLOAD(offset=0xB1500))
        + Op.SSTORE(key=0xA16, value=Op.MLOAD(offset=0xA1600))
        + Op.SSTORE(key=0xB16, value=Op.MLOAD(offset=0xB1600))
        + Op.SSTORE(key=0xA17, value=Op.MLOAD(offset=0xA1700))
        + Op.SSTORE(key=0xB17, value=Op.MLOAD(offset=0xB1700))
        + Op.SSTORE(key=0xA18, value=Op.MLOAD(offset=0xA1800))
        + Op.SSTORE(key=0xB18, value=Op.MLOAD(offset=0xB1800))
        + Op.SSTORE(key=0xA19, value=Op.MLOAD(offset=0xA1900))
        + Op.SSTORE(key=0xB19, value=Op.MLOAD(offset=0xB1900))
        + Op.SSTORE(key=0xA20, value=Op.MLOAD(offset=0xA2000))
        + Op.SSTORE(key=0xB20, value=Op.MLOAD(offset=0xB2000))
        + Op.STOP,
        storage={
            0: 0xDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAF,  # noqa: E501
            1: 0xDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAFDEADBEAF,  # noqa: E501
        },
        balance=1000,
        nonce=0,
        address=Address(0xB000000000000000000000000000000000000000),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=4000000,
        value=100,
    )

    post = {
        contract_1: Account(storage={}, balance=1000),
        contract_0: Account(
            storage={
                0: 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED,  # noqa: E501
                1: 0xFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEEDFEED,  # noqa: E501
                2560: 1,
                2561: sender,
                2562: 1,
                2563: 1,
                2564: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2565: 0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
                2566: 1,
                2567: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2568: 0x14EF238CFA4075E9EDE92F18B1566C1DD0B99AAA,
                2569: 1,
                2576: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2577: 1,
                2578: 1,
                2579: 1,
                2580: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                2581: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                2582: 1,
                2583: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                2584: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                2585: 1,
                2592: 1,
                2816: 1,
                2817: sender,
                2818: 1,
                2819: 1,
                2820: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2821: 0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
                2822: 1,
                2823: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2824: 0x14EF238CFA4075E9EDE92F18B1566C1DD0B99AAA,
                2825: 1,
                2832: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                2833: 1,
                2834: 1,
                2835: 1,
                2836: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                2837: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                2838: 1,
                2839: 0x1F4D1D80177B1377743D1901F70D7389BE7F7A35A35BFD234A8AAEE615B88C49,  # noqa: E501
                2840: 0x18683193AE021A2F8920FED186CDE5D9B1365116865281CCF884C1F28B1DF8F,  # noqa: E501
                2841: 1,
                2848: 1,
            },
            balance=1100,
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
