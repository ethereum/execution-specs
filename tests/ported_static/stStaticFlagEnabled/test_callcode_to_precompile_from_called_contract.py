"""
Contract C calls contract B.
Contract B staticcalls contract A.
Contract A callcodes precompiled contracts.
It should execute successfully for each precompiled contract.


Ported from:
state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromCalledContractFiller.yml
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
    ["state_tests/stStaticFlagEnabled/CallcodeToPrecompileFromCalledContractFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcode_to_precompile_from_called_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Contract C calls contract B."""
    coinbase = Address("0xcafe000000000000000000000000000000000001")
    contract_0 = Address("0xc000000000000000000000000000000000000000")
    contract_1 = Address("0xb000000000000000000000000000000000000000")
    contract_2 = Address("0xa000000000000000000000000000000000000000")
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
    #   (CALL (GAS) 0xb000000000000000000000000000000000000000 0 0 0 0 0)
    #   [[ 0x01 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.POP(Op.CALL(gas=Op.GAS, address=0xb000000000000000000000000000000000000000, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.STOP,
        storage={
            0: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf,
            1: 0xdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeafdeadbeaf,
        },
        balance=1000,
        nonce=0,
        address=Address("0xc000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: lll
    # {
    #   [[ 0x00 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
    #   (STATICCALL (GAS) 0xa000000000000000000000000000000000000000 0 0 0x0a0000 0x012020)
    #   [[ 0x01 ]] 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed
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
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.POP(Op.STATICCALL(gas=Op.GAS, address=0xa000000000000000000000000000000000000000, args_offset=0x0, args_size=0x0, ret_offset=0xa0000, ret_size=0x12020))
        + Op.SSTORE(key=0x1, value=0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed)  # noqa: E501
        + Op.SSTORE(key=0xa00, value=Op.MLOAD(offset=0xa0000))
        + Op.SSTORE(key=0xb00, value=Op.MLOAD(offset=0xb0000))
        + Op.SSTORE(key=0xa01, value=Op.MLOAD(offset=0xa0100))
        + Op.SSTORE(key=0xb01, value=Op.MLOAD(offset=0xb0100))
        + Op.SSTORE(key=0xa02, value=Op.MLOAD(offset=0xa0200))
        + Op.SSTORE(key=0xb02, value=Op.MLOAD(offset=0xb0200))
        + Op.SSTORE(key=0xa03, value=Op.MLOAD(offset=0xa0300))
        + Op.SSTORE(key=0xb03, value=Op.MLOAD(offset=0xb0300))
        + Op.SSTORE(key=0xa04, value=Op.MLOAD(offset=0xa0400))
        + Op.SSTORE(key=0xb04, value=Op.MLOAD(offset=0xb0400))
        + Op.SSTORE(key=0xa05, value=Op.MLOAD(offset=0xa0500))
        + Op.SSTORE(key=0xb05, value=Op.MLOAD(offset=0xb0500))
        + Op.SSTORE(key=0xa06, value=Op.MLOAD(offset=0xa0600))
        + Op.SSTORE(key=0xb06, value=Op.MLOAD(offset=0xb0600))
        + Op.SSTORE(key=0xa07, value=Op.MLOAD(offset=0xa0700))
        + Op.SSTORE(key=0xb07, value=Op.MLOAD(offset=0xb0700))
        + Op.SSTORE(key=0xa08, value=Op.MLOAD(offset=0xa0800))
        + Op.SSTORE(key=0xb08, value=Op.MLOAD(offset=0xb0800))
        + Op.SSTORE(key=0xa09, value=Op.MLOAD(offset=0xa0900))
        + Op.SSTORE(key=0xb09, value=Op.MLOAD(offset=0xb0900))
        + Op.SSTORE(key=0xa10, value=Op.MLOAD(offset=0xa1000))
        + Op.SSTORE(key=0xb10, value=Op.MLOAD(offset=0xb1000))
        + Op.SSTORE(key=0xa11, value=Op.MLOAD(offset=0xa1100))
        + Op.SSTORE(key=0xb11, value=Op.MLOAD(offset=0xb1100))
        + Op.SSTORE(key=0xa12, value=Op.MLOAD(offset=0xa1200))
        + Op.SSTORE(key=0xb12, value=Op.MLOAD(offset=0xb1200))
        + Op.SSTORE(key=0xa13, value=Op.MLOAD(offset=0xa1300))
        + Op.SSTORE(key=0xb13, value=Op.MLOAD(offset=0xb1300))
        + Op.SSTORE(key=0xa14, value=Op.MLOAD(offset=0xa1400))
        + Op.SSTORE(key=0xb14, value=Op.MLOAD(offset=0xb1400))
        + Op.SSTORE(key=0xa15, value=Op.MLOAD(offset=0xa1500))
        + Op.SSTORE(key=0xb15, value=Op.MLOAD(offset=0xb1500))
        + Op.SSTORE(key=0xa16, value=Op.MLOAD(offset=0xa1600))
        + Op.SSTORE(key=0xb16, value=Op.MLOAD(offset=0xb1600))
        + Op.SSTORE(key=0xa17, value=Op.MLOAD(offset=0xa1700))
        + Op.SSTORE(key=0xb17, value=Op.MLOAD(offset=0xb1700))
        + Op.SSTORE(key=0xa18, value=Op.MLOAD(offset=0xa1800))
        + Op.SSTORE(key=0xb18, value=Op.MLOAD(offset=0xb1800))
        + Op.SSTORE(key=0xa19, value=Op.MLOAD(offset=0xa1900))
        + Op.SSTORE(key=0xb19, value=Op.MLOAD(offset=0xb1900))
        + Op.SSTORE(key=0xa20, value=Op.MLOAD(offset=0xa2000))
        + Op.SSTORE(key=0xb20, value=Op.MLOAD(offset=0xb2000)) + Op.STOP,
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
    contract_2 = pre.deploy_contract(
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
        data=b'',
        gas_limit=4000000,
        value=100,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_2: Account(storage={}, balance=1000),
        contract_0: Account(
                storage={
            0: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
            1: 0xfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeedfeed,
        },
                balance=1100,
            ),
        contract_1: Account(
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
                balance=1000,
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
