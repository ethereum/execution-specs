"""
Test_ecrecover_short_buff.

Ported from:
state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml
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
    ["state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ecrecover_short_buff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_ecrecover_short_buff."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=71794957647893862,
    )

    # Source: yul
    # berlin
    # {
    #   let maxLength := 0xA0
    #
    #   // Initialization
    #   for { let i := 0 } lt(i, maxLength) { i := add(i, 1) } {
    #      // Initialize storage to verify it gets overwritten
    #      sstore(i, 0xdead60A7)
    #      sstore(add(0x1000,i), 0xdead60A7)
    #   }
    #
    #   // Create a legitimate signature
    #   mstore(0, 0)
    #
    #   // The signature (for zero)
    #   mstore(0x20, 27)  // v
    #   mstore(0x40, 0x184870a8e4faa6065ddf65c873935d3e48e3d1c7b7853f25cd79b8247f771910) // r  # noqa: E501
    #   mstore(0x60, 0x226140b6b66554c7fcfa38589e433cc148ebe5c8482eb3093ab1d9a932c96f58) // s  # noqa: E501
    #
    #
    #
    #   // Call ecrecover with every possible length that's too short, the right length  # noqa: E501
    #   // (0x80), and some excessive lengths
    #   for { let len := 0 } lt(len, maxLength) { len := add(len,1) } {
    #      // Call ecrecoer
    #      sstore(len, call(gas(), 1, 0, 0, len, 0x100, 0x20))
    #
    #      // The expected retval is one, so to avoid specifying every length
    #      // in the expect: section we subtract one.
    #      sstore(len, sub(sload(len), 1))
    # ... (5 more lines)
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0xA0]
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x8A, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.POP
        + Op.MSTORE(offset=Op.DUP1, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x1B)
        + Op.MSTORE(
            offset=0x40,
            value=0x184870A8E4FAA6065DDF65C873935D3E48E3D1C7B7853F25CD79B8247F771910,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x60,
            value=0x226140B6B66554C7FCFA38589E433CC148EBE5C8482EB3093AB1D9A932C96F58,  # noqa: E501
        )
        + Op.PUSH1[0x0]
        + Op.JUMPDEST
        + Op.JUMPI(pc=0x67, condition=Op.LT(Op.DUP2, Op.DUP2))
        + Op.STOP
        + Op.JUMPDEST
        + Op.DUP1
        + Op.PUSH1[0x20]
        + Op.PUSH2[0x100]
        + Op.PUSH1[0x1]
        + Op.SWAP4
        + Op.PUSH1[0x0]
        + Op.DUP1
        + Op.DUP7
        + Op.GAS
        + Op.CALL
        + Op.DUP3
        + Op.SWAP1
        + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.SSTORE(key=Op.ADD(Op.DUP3, 0x1000), value=Op.MLOAD(offset=0x100))
        + Op.ADD
        + Op.JUMP(pc=0x5F)
        + Op.JUMPDEST
        + Op.PUSH4[0xDEAD60A7]
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1)
        + Op.ADD(Op.DUP3, 0x1000)
        + Op.SSTORE
        + Op.PUSH1[0x1]
        + Op.ADD
        + Op.JUMP(pc=0x4),
        storage={
            0: 24743,
            17: 24743,
            34: 24743,
            51: 24743,
            68: 24743,
            85: 24743,
            102: 24743,
            119: 24743,
            128: 24743,
            153: 24743,
            4096: 24743,
            4113: 24743,
            4130: 24743,
            4147: 24743,
            4164: 24743,
            4181: 24743,
            4198: 24743,
            4215: 24743,
            4224: 24743,
            4249: 24743,
        },
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000, nonce=1)

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes("00"),
        gas_limit=7400000,
        value=0x186A0,
        nonce=1,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0,
                1: 0,
                159: 0,
                4096: 0,
                4112: 0,
                4144: 0,
                4192: 0,
                4193: 0x8E5817968F74FFB0255AE41EEFA6F89DD0183FA1,
                4194: 0xB7529ED60A10291754A635ED9FD67C1723F4D83B,
                4195: 0x669457CE81442F235FFC4123662BA14A72B3D68,
                4196: 0xDCC53A4A0719101437E8791ABF273AF5893CB174,
                4197: 0xA1889691E30136D95C0543F516BF2357B282D835,
                4198: 0x6642C4FD062A12B980D2BF28334E48FFE609248,
                4199: 0x628F176BC4C64973ABAF9ACB6BD8BB8D9B1AE97C,
                4200: 0x16FE7FA0CB8A861F855039C2EDA9251CA7CC79D0,
                4201: 0x1C954021193A220878900CF5F7DB5B3EA4C2B24,
                4202: 0x5C4725E00D8F9415E2B77630543FE41DCDAAA304,
                4203: 0xF6DEFD0F92F2A018BA20BF6051698A8DDE7CC949,
                4204: 0x99CD51158E59DA36BA48B457C02DB77C17A6B91A,
                4205: 0xFC4539330FEE551B296F9396D01AB7643521D5DF,
                4206: 0x389A57BA1C546578B67167C6571D92E047BD4029,
                4207: 0x294091B609877B020B4F5A01357936FC0A877A3F,
                4208: 0xAD5A9FC193DCF16041D4E96433EF3A6D82D36B16,
                4209: 0x8324683AAAE32CCEBDEB758E2777AB2B1CE3D3F1,
                4210: 0x295AD34CB312EAF9574511208848CAF57B7429E0,
                4211: 0xA74178EC0A865B84EED705E85DDF9B5002389AB,
                4212: 0xD1D3BC125318DD71176248D9C86F41A842D4BEC9,
                4213: 0xE8E2D3E49D1BB0DDF5BEEFF311456F251DAE9EA9,
                4214: 0xD8765900C0F467DF6BC4F514ED39C568497A8EAD,
                4215: 0xDB658A31F5A174BE0E3FC0D0CE05DD6A76084910,
                4216: 0x1387AF122C1E31A2DD1DAC303B3F20AD83F0ED1B,
                4217: 0x9CA540E3F00347324BD94A94CE8E3A34B97C8244,
                4218: 0x8D682238981C4940830FA6971D25E036D1FB3D27,
                4219: 0xF571EB5ABD7DA99C6B32B3F3ED0740F6FAC7D14B,
                4220: 0x79E727F2F0F816EFD56FC2AF37D98AF6798551DF,
                4221: 0xF00D6A30E65104B909AA43D947EF2010E09446A,
                4222: 0x4C78739DE03A70DBCF9B94BC21DAF2BF46D44375,
                4223: 0x364A9DAE48110760306B009BF2297819176BE559,
                4224: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4225: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4226: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4227: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4228: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4229: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4230: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4231: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4232: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4233: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4234: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4235: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4236: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4237: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4238: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4239: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4240: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4241: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4242: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4243: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4244: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4245: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4246: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4247: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4248: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4249: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4250: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4251: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4252: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4253: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4254: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
                4255: 0x3F9ECB7B25FA567AFB2A4C7B633749BDA578B593,
            },
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
