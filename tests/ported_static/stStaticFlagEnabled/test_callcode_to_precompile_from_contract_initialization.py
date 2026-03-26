"""
Contract B creates new contract.
New contract initialization code staticcalls contract A.
Contract A callcodes precompiled contracts.
It should execute successfully for each precompiled contract.


Ported from:
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromContractInitializationFiller.yml
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
    ["state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromContractInitializationFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_to_precompile_from_contract_initialization(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Contract B creates new contract."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    contract_0 = Address("0xb000000000000000000000000000000000000000")
    contract_1 = Address("0xa000000000000000000000000000000000000000")
    sender = EOA(
        key=0x45a915e4d060149eb4365960e6a7a45f334393093061116b197e3240065ff2d8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: lll
    # {
    #   [[ 0x00 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    #   (CALLDATACOPY 0 0 (CALLDATASIZE))
    #   [[ 0x01 ]] (CREATE2 0 0 (CALLDATASIZE) 0x5a175a17)
    #   [[ 0x02 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.CALLDATACOPY(dest_offset=0x0, offset=0x0, size=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x1, value=Op.CREATE2(value=0x0, offset=0x0, size=Op.CALLDATASIZE, salt=0x5a175a17))  # noqa: E501
        + Op.SSTORE(key=0x2, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.STOP,
        storage={
            0: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf,
            1: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf,
        },
        balance=1000,
        nonce=0,
        address=Address("0xb000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {
    #   ;; Recovery of ECDSA signature
    #   [ 0x00 ] 0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c
    #   [ 0x20 ] 28
    #   [ 0x40 ] 0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f
    #   [ 0x60 ] 0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549
    #   ;; zero value
    #   [ 0x0a0000 ] (CALLCODE (GAS) 1 0 0 128 0x2000 32)
    #   [ 0x0a0100 ] (MOD @0x2000 (EXP 2 160))
    #   [ 0x0a0200 ] (EQ (ORIGIN) @0x0a0100)
    #   [ 0x2000 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   ;; non zero value
    #   [ 0x0b0000 ] (CALLCODE (GAS) 1 1 0 128 0x2020 32)
    #   [ 0x0b0100 ] (MOD @0x2020 (EXP 2 160))
    #   [ 0x0b0200 ] (EQ (ORIGIN) @0x0b0100)
    #   [ 0x00 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   [ 0x20 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   [ 0x40 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   [ 0x60 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   [ 0x2020 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    # 
    #   ;; Hash function SHA256
    #   [ 0x00 ] 0x0000000ccccccccccccccccccccccccccccccccccccccccccccccccccc000000
    #   ;; zero value
    #   [ 0x0a0300 ] (CALLCODE (GAS) 2 0 0 32 0x2000 32)
    #   [ 0x0a0400 ] @0
    #   [ 0x0a0500 ] @0x2000
    #   [ 0x2000 ] 0x0000000000000000000000000000000000000000000000000000000000000000
    #   ;; non zero value
    #   [ 0x0b0300 ] (CALLCODE (GAS) 2 1 0 32 0x2020 32)
    # ... (121 more lines)
    contract_1 = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x18c547e4f7b0f325ad1e56f57e26c745b09a3e503d86e00e5255ff7f715d3d1c)
        + Op.MSTORE(offset=0x20, value=0x1c)
        + Op.MSTORE(offset=0x40, value=0x73b1693892219d736caba55bdb67216e485557ea6b6af75f37096c9aa6a5a75f)
        + Op.MSTORE(offset=0x60, value=0xeeb940b1d03b21e36b0e47e79769f095fe2ab855bd91e3a38756b7d75a9c4549)
        + Op.MSTORE(offset=0xa0000, value=Op.CALLCODE(gas=Op.GAS, address=0x1, value=0x0, args_offset=0x0, args_size=0x80, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa0100, value=Op.MOD(Op.MLOAD(offset=0x2000), Op.EXP(0x2, 0xa0)))
        + Op.MSTORE(offset=0xa0200, value=Op.EQ(Op.ORIGIN, Op.MLOAD(offset=0xa0100)))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb0000, value=Op.CALLCODE(gas=Op.GAS, address=0x1, value=0x1, args_offset=0x0, args_size=0x80, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb0100, value=Op.MOD(Op.MLOAD(offset=0x2020), Op.EXP(0x2, 0xa0)))
        + Op.MSTORE(offset=0xb0200, value=Op.EQ(Op.ORIGIN, Op.MLOAD(offset=0xb0100)))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0) + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000)
        + Op.MSTORE(offset=0xa0300, value=Op.CALLCODE(gas=Op.GAS, address=0x2, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa0400, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xa0500, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb0300, value=Op.CALLCODE(gas=Op.GAS, address=0x2, value=0x1, args_offset=0x0, args_size=0x20, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb0400, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xb0500, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000)
        + Op.MSTORE(offset=0xa0600, value=Op.CALLCODE(gas=Op.GAS, address=0x3, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa0700, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xa0800, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb0600, value=Op.CALLCODE(gas=Op.GAS, address=0x3, value=0x1, args_offset=0x0, args_size=0x20, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb0700, value=Op.MLOAD(offset=0x0))
        + Op.MSTORE(offset=0xb0800, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000)
        + Op.MSTORE(offset=0xa0900, value=Op.CALLCODE(gas=Op.GAS, address=0x4, value=0x0, args_offset=0x0, args_size=0x20, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa1000, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb0900, value=Op.CALLCODE(gas=Op.GAS, address=0x4, value=0x1, args_offset=0x0, args_size=0x20, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb1000, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0x1) + Op.MSTORE(offset=0x20, value=0x20)
        + Op.MSTORE(offset=0x40, value=0x20)
        + Op.MSTORE(offset=0x60, value=0x3fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc)
        + Op.MSTORE(offset=0x80, value=0x2efffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc)
        + Op.MSTORE(offset=0xa0, value=0x2f00000000000000000000000000000000000000000000000000000000000000)
        + Op.MSTORE(offset=0xa1100, value=Op.CALLCODE(gas=Op.GAS, address=0x5, value=0x0, args_offset=0x0, args_size=0xa1, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa1200, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb1100, value=Op.CALLCODE(gas=Op.GAS, address=0x5, value=0x1, args_offset=0x0, args_size=0xa1, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb1200, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0) + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x80, value=0x0) + Op.MSTORE(offset=0xa0, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0xf25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2)
        + Op.MSTORE(offset=0x20, value=0x16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba)
        + Op.MSTORE(offset=0x40, value=0x1de49a4b0233273bba8146af82042d004f2085ec982397db0d97da17204cc286)
        + Op.MSTORE(offset=0x60, value=0x217327ffc463919bef80cc166d09c6172639d8589799928761bcd9f22c903d4)
        + Op.MSTORE(offset=0xa1300, value=Op.CALLCODE(gas=Op.GAS, address=0x6, value=0x0, args_offset=0x0, args_size=0x80, ret_offset=0x2000, ret_size=0x40))
        + Op.MSTORE(offset=0xa1400, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0xa1500, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0xb1300, value=Op.CALLCODE(gas=Op.GAS, address=0x6, value=0x1, args_offset=0x0, args_size=0x80, ret_offset=0x3000, ret_size=0x40))
        + Op.MSTORE(offset=0xb1400, value=Op.MLOAD(offset=0x3000))
        + Op.MSTORE(offset=0xb1500, value=Op.MLOAD(offset=0x3020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0) + Op.MSTORE(offset=0x60, value=0x0)
        + Op.MSTORE(offset=0x3000, value=0x0)
        + Op.MSTORE(offset=0x3020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0xf25929bcb43d5a57391564615c9e70a992b10eafa4db109709649cf48c50dd2)
        + Op.MSTORE(offset=0x20, value=0x16da2f5cb6be7a0aa72c440c53c9bbdfec6c36c7d515536431b3a865468acbba)
        + Op.MSTORE(offset=0x40, value=0x3)
        + Op.MSTORE(offset=0xa1600, value=Op.CALLCODE(gas=Op.GAS, address=0x7, value=0x0, args_offset=0x0, args_size=0x60, ret_offset=0x2000, ret_size=0x40))
        + Op.MSTORE(offset=0xa1700, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0xa1800, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.MSTORE(offset=0xb1600, value=Op.CALLCODE(gas=Op.GAS, address=0x7, value=0x1, args_offset=0x0, args_size=0x60, ret_offset=0x3000, ret_size=0x40))
        + Op.MSTORE(offset=0xb1700, value=Op.MLOAD(offset=0x3000))
        + Op.MSTORE(offset=0xb1800, value=Op.MLOAD(offset=0x3020))
        + Op.MSTORE(offset=0x0, value=0x0) + Op.MSTORE(offset=0x20, value=0x0)
        + Op.MSTORE(offset=0x40, value=0x0) + Op.MSTORE(offset=0x3000, value=0x0)
        + Op.MSTORE(offset=0x3020, value=0x0)
        + Op.MSTORE(offset=0x0, value=0x1c76476f4def4bb94541d57ebba1193381ffa7aa76ada664dd31c16024c43f59)
        + Op.MSTORE(offset=0x20, value=0x3034dd2920f673e204fee2811c678745fc819b55d3e9d294e45c9b03a76aef41)
        + Op.MSTORE(offset=0x40, value=0x209dd15ebff5d46c4bd888e51a93cf99a7329636c63514396b4a452003a35bf7)
        + Op.MSTORE(offset=0x60, value=0x4bf11ca01483bfa8b34b43561848d28905960114c8ac04049af4b6315a41678)
        + Op.MSTORE(offset=0x80, value=0x2bb8324af6cfc93537a2ad1a445cfd0ca2a71acd7ac41fadbf933c2a51be344d)
        + Op.MSTORE(offset=0xa0, value=0x120a2a4cf30c1bf9845f20c6fe39e07ea2cce61f0c9bb048165fe5e4de877550)
        + Op.MSTORE(offset=0xc0, value=0x111e129f1cf1097710d41c4ac70fcdfa5ba2023c6ff1cbeac322de49d1b6df7c)
        + Op.MSTORE(offset=0xe0, value=0x2032c61a830e3c17286de9462bf242fca2883585b93870a73853face6a6bf411)
        + Op.MSTORE(offset=0x100, value=0x198e9393920d483a7260bfb731fb5d25f1aa493335a9e71297e485b7aef312c2)
        + Op.MSTORE(offset=0x120, value=0x1800deef121f1e76426a00665e5c4479674322d4f75edadd46debd5cd992f6ed)
        + Op.MSTORE(offset=0x140, value=0x90689d0585ff075ec9e99ad690c3395bc4b313370b38ef355acdadcd122975b)
        + Op.MSTORE(offset=0x160, value=0x12c85ea5db8c6deb4aab71808dcb408fe3d1e7690c43d37b4ce6cc0166fa7daa)
        + Op.MSTORE(offset=0xa1900, value=Op.CALLCODE(gas=Op.GAS, address=0x8, value=0x0, args_offset=0x0, args_size=0x180, ret_offset=0x2000, ret_size=0x20))
        + Op.MSTORE(offset=0xa2000, value=Op.MLOAD(offset=0x2000))
        + Op.MSTORE(offset=0x2000, value=0x0)
        + Op.MSTORE(offset=0xb1900, value=Op.CALLCODE(gas=Op.GAS, address=0x8, value=0x1, args_offset=0x0, args_size=0x180, ret_offset=0x2020, ret_size=0x20))
        + Op.MSTORE(offset=0xb2000, value=Op.MLOAD(offset=0x2020))
        + Op.MSTORE(offset=0x2020, value=0x0)
        + Op.RETURN(offset=0xa0000, size=0x12020) + Op.STOP,
        balance=1000,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=bytes.fromhex("7ffeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed60005562012020620a00006000600073a0000000000000000000000000000000000000005afa507ffeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed600155620a000051610a0055620b000051610b0055620a010051610a0155620b010051610b0155620a020051610a0255620b020051610b0255620a030051610a0355620b030051610b0355620a040051610a0455620b040051610b0455620a050051610a0555620b050051610b0555620a060051610a0655620b060051610b0655620a070051610a0755620b070051610b0755620a080051610a0855620b080051610b0855620a090051610a0955620b090051610b0955620a100051610a1055620b100051610b1055620a110051610a1155620b110051610b1155620a120051610a1255620b120051610b1255620a130051610a1355620b130051610b1355620a140051610a1455620b140051610b1455620a150051610a1555620b150051610b1555620a160051610a1655620b160051610b1655620a170051610a1755620b170051610b1755620a180051610a1855620b180051610b1855620a190051610a1955620b190051610b1955620a200051610a2055620b200051610b205500"),  # noqa: E501
        gas_limit=4000000,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
            1: 0xb2bc42a2d3b34f228ba399e53ab6f1b3d2672177,
            2: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
        },
                balance=1100,
            ),
        Address("0xb2bc42a2d3b34f228ba399e53ab6f1b3d2672177"): Account(
                storage={
            0: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
            1: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
            2560: 1,
            2561: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            2562: 1,
            2563: 1,
            2564: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2565: 0x73f5062fb68ed2a1ec82ff8c73f9251bb9cf53a623bc93527e16bc5ae29dad74,
            2566: 1,
            2567: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2568: 0x14ef238cfa4075e9ede92f18b1566c1dd0b99aaa,
            2569: 1,
            2576: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2577: 1,
            2578: 1,
            2579: 1,
            2580: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            2581: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
            2582: 1,
            2583: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            2584: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
            2585: 1,
            2592: 1,
            2816: 1,
            2817: 0xa94f5374fce5edbc8e2a8697c15331677e6ebf0b,
            2818: 1,
            2819: 1,
            2820: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2821: 0x73f5062fb68ed2a1ec82ff8c73f9251bb9cf53a623bc93527e16bc5ae29dad74,
            2822: 1,
            2823: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2824: 0x14ef238cfa4075e9ede92f18b1566c1dd0b99aaa,
            2825: 1,
            2832: 0xccccccccccccccccccccccccccccccccccccccccccccccccccc000000,
            2833: 1,
            2834: 1,
            2835: 1,
            2836: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            2837: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
            2838: 1,
            2839: 0x1f4d1d80177b1377743d1901f70d7389be7f7a35a35bfd234a8aaee615b88c49,
            2840: 0x18683193ae021a2f8920fed186cde5d9b1365116865281ccf884c1f28b1df8f,
            2841: 1,
            2848: 1,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
