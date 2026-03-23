"""
STATICCALL to precompiled contracts from contract that called from another...

It should execute successfully for each precompiled contract.

Ported from:
tests/static/state_tests/stStaticCall
StaticcallToPrecompileFromCalledContractFiller.yml
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stStaticCall/StaticcallToPrecompileFromCalledContractFiller.yml",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
@pytest.mark.slow
def test_staticcall_to_precompile_from_called_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """STATICCALL to precompiled contracts from contract that called..."""
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
    callee = pre.deploy_contract(
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
    # Source: LLL
    # {
    #   [[ 0 ]] (CALL (GAS) 0xa000000000000000000000000000000000000000 0 0 0 0 0 )  # noqa: E501
    # }
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.CALL(
                    gas=Op.GAS,
                    address=0xA000000000000000000000000000000000000000,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={
                        0: 1,
                        1: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        2: 1,
                        3: 1,
                        4: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
                        5: 0x73F5062FB68ED2A1EC82FF8C73F9251BB9CF53A623BC93527E16BC5AE29DAD74,  # noqa: E501
                        6: 1,
                        7: 0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC000000,  # noqa: E501
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
                    code=bytes.fromhex(
                        "7f18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c600052601c6020527f73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f6040527feeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c454960605260206103e86080600060015afa60005560a060020a6103e851066001556001543214600255600060005260006020526000604052600060605260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060025afa6003556000516004556103e851600555600060005260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060035afa6006556000516007556103e851600855600060005260006103e8527c0ccccccccccccccccccccccccccccccccccccccccccccccccccc00000060005260206103e86020600060045afa6009556103e851601055600060005260006103e8526001600052602060205260206040527f03fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6060527f2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc6080527f2f0000000000000000000000000000000000000000000000000000000000000060a05260206103e860a1600060055afa6011556103e85160125560006000526000602052600060405260006060526000608052600060a05260006103e8527f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba6020527f1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc2866040527f0217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d460605260406103e86080600060065afa6013556103e85160145561040851601555600060005260006020526000604052600060605260006103e8526000610408527f0f25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd26000527f16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba602052600360405260406103e86060600060075afa6016556103e8516017556104085160185560006000526000602052600060405260006103e8526000610408527f1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f596000527f3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef416020527f209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf76040527f04bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a416786060527f2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d6080527f120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de87755060a0527f111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c60c0527f2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf41160e0527f198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2610100527f1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed610120527f090689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b610140527f12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa6101605260206103e8610180600060085afa6019556103e85160205500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    storage={0: 1},
                    code=bytes.fromhex(
                        "6000600060006000600073a0000000000000000000000000000000000000005af160005500"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=1000000,
        value=100,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
