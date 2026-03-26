"""
test_ecrecover_short_buff

Ported from:
state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml
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
    ["state_tests/stPreCompiledContracts2/ecrecoverShortBuffFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_ecrecover_short_buff(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_ecrecover_short_buff"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xcccccccccccccccccccccccccccccccccccccccc")
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
    #   mstore(0x40, 0x184870a8e4faa6065ddf65c873935d3e48e3d1c7b7853f25cd79b8247f771910) // r
    #   mstore(0x60, 0x226140b6b66554c7fcfa38589e433cc148ebe5c8482eb3093ab1d9a932c96f58) // s
    # 
    # 
    # 
    #   // Call ecrecover with every possible length that's too short, the right length
    #   // (0x80), and some excessive lengths
    #   for { let len := 0 } lt(len, maxLength) { len := add(len,1) } {
    #      // Call ecrecoer
    #      sstore(len, call(gas(), 1, 0, 0, len, 0x100, 0x20))
    # 
    #      // The expected retval is one, so to avoid specifying every length
    #      // in the expect: section we subtract one.
    #      sstore(len, sub(sload(len), 1))
    # ... (5 more lines)
    contract_0 = pre.deploy_contract(
        code=Op.PUSH1[0xa0] + Op.PUSH1[0x0] + Op.JUMPDEST
        + Op.JUMPI(pc=0x8a, condition=Op.LT(Op.DUP2, Op.DUP2)) + Op.POP
        + Op.MSTORE(offset=Op.DUP1, value=0x0)
        + Op.MSTORE(offset=0x20, value=0x1b)
        + Op.MSTORE(offset=0x40, value=0x184870a8e4faa6065ddf65c873935d3e48e3d1c7b7853f25cd79b8247f771910)
        + Op.MSTORE(offset=0x60, value=0x226140b6b66554c7fcfa38589e433cc148ebe5c8482eb3093ab1d9a932c96f58)
        + Op.PUSH1[0x0] + Op.JUMPDEST
        + Op.JUMPI(pc=0x67, condition=Op.LT(Op.DUP2, Op.DUP2)) + Op.STOP
        + Op.JUMPDEST + Op.DUP1 + Op.PUSH1[0x20] + Op.PUSH2[0x100]
        + Op.PUSH1[0x1] + Op.SWAP4 + Op.PUSH1[0x0] + Op.DUP1 + Op.DUP7 + Op.GAS
        + Op.CALL + Op.DUP3 + Op.SWAP1 + Op.SSTORE(key=Op.DUP2, value=Op.SUB)
        + Op.SSTORE(key=Op.ADD(Op.DUP3, 0x1000), value=Op.MLOAD(offset=0x100))
        + Op.ADD + Op.JUMP(pc=0x5f) + Op.JUMPDEST + Op.PUSH4[0xdead60a7]
        + Op.SSTORE(key=Op.DUP3, value=Op.DUP1) + Op.ADD(Op.DUP3, 0x1000)
        + Op.SSTORE + Op.PUSH1[0x1] + Op.ADD + Op.JUMP(pc=0x4),
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
        address=Address("0xcccccccccccccccccccccccccccccccccccccccc"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000, nonce=1)


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=bytes.fromhex("00"),
        gas_limit=7400000,
        value=0x186a0,
        nonce=1,
        gas_price=10,
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
            4193: 0x8e5817968f74ffb0255ae41eefa6f89dd0183fa1,
            4194: 0xb7529ed60a10291754a635ed9fd67c1723f4d83b,
            4195: 0x669457ce81442f235ffc4123662ba14a72b3d68,
            4196: 0xdcc53a4a0719101437e8791abf273af5893cb174,
            4197: 0xa1889691e30136d95c0543f516bf2357b282d835,
            4198: 0x6642c4fd062a12b980d2bf28334e48ffe609248,
            4199: 0x628f176bc4c64973abaf9acb6bd8bb8d9b1ae97c,
            4200: 0x16fe7fa0cb8a861f855039c2eda9251ca7cc79d0,
            4201: 0x1c954021193a220878900cf5f7db5b3ea4c2b24,
            4202: 0x5c4725e00d8f9415e2b77630543fe41dcdaaa304,
            4203: 0xf6defd0f92f2a018ba20bf6051698a8dde7cc949,
            4204: 0x99cd51158e59da36ba48b457c02db77c17a6b91a,
            4205: 0xfc4539330fee551b296f9396d01ab7643521d5df,
            4206: 0x389a57ba1c546578b67167c6571d92e047bd4029,
            4207: 0x294091b609877b020b4f5a01357936fc0a877a3f,
            4208: 0xad5a9fc193dcf16041d4e96433ef3a6d82d36b16,
            4209: 0x8324683aaae32ccebdeb758e2777ab2b1ce3d3f1,
            4210: 0x295ad34cb312eaf9574511208848caf57b7429e0,
            4211: 0xa74178ec0a865b84eed705e85ddf9b5002389ab,
            4212: 0xd1d3bc125318dd71176248d9c86f41a842d4bec9,
            4213: 0xe8e2d3e49d1bb0ddf5beeff311456f251dae9ea9,
            4214: 0xd8765900c0f467df6bc4f514ed39c568497a8ead,
            4215: 0xdb658a31f5a174be0e3fc0d0ce05dd6a76084910,
            4216: 0x1387af122c1e31a2dd1dac303b3f20ad83f0ed1b,
            4217: 0x9ca540e3f00347324bd94a94ce8e3a34b97c8244,
            4218: 0x8d682238981c4940830fa6971d25e036d1fb3d27,
            4219: 0xf571eb5abd7da99c6b32b3f3ed0740f6fac7d14b,
            4220: 0x79e727f2f0f816efd56fc2af37d98af6798551df,
            4221: 0xf00d6a30e65104b909aa43d947ef2010e09446a,
            4222: 0x4c78739de03a70dbcf9b94bc21daf2bf46d44375,
            4223: 0x364a9dae48110760306b009bf2297819176be559,
            4224: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4225: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4226: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4227: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4228: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4229: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4230: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4231: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4232: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4233: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4234: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4235: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4236: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4237: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4238: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4239: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4240: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4241: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4242: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4243: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4244: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4245: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4246: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4247: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4248: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4249: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4250: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4251: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4252: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4253: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4254: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
            4255: 0x3f9ecb7b25fa567afb2a4c7b633749bda578b593,
        },
            ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
