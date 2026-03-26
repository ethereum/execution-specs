"""
test_callcallcode_01

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json
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
    ["state_tests/stCallDelegateCodesCallCodeHomestead/callcallcode_01Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcode_01(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_callcallcode_01"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xe04d1ac7ddda0c98397d56a0b501e960d4cd325a39286919ac23c1a07009a869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALLCODE 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x55730, address=0x1ccccf19d84280c8a0e94209761296dabd87b3c9, value=0x1, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xdb43306b16c521b9cc3667fbe7d1b697bb1f9605"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 250000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.DELEGATECALL(gas=0x3d090, address=0xd42cd48f1d9a88f4b75bfb5e46e754c1128bd7fb, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0x1ccccf19d84280c8a0e94209761296dabd87b3c9"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 2 1) (SSTORE 4 (CALLER)) (SSTORE 5 (CALLVALUE)) (SSTORE 230 (ADDRESS)) (SSTORE 232 (ORIGIN)) (SSTORE 236 (CALLDATASIZE)) (SSTORE 238 (CODESIZE)) (SSTORE 240 (GASPRICE)) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.SSTORE(key=0x2, value=0x1) + Op.SSTORE(key=0x4, value=Op.CALLER)  # noqa: E501
        + Op.SSTORE(key=0x5, value=Op.CALLVALUE)
        + Op.SSTORE(key=0xe6, value=Op.ADDRESS)
        + Op.SSTORE(key=0xe8, value=Op.ORIGIN)
        + Op.SSTORE(key=0xec, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0xee, value=Op.CODESIZE)
        + Op.SSTORE(key=0xf0, value=Op.GASPRICE) + Op.STOP,
        nonce=0,
        address=Address("0xd42cd48f1d9a88f4b75bfb5e46e754c1128bd7fb"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=3000000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(
                storage={
            0: 1,
            1: 1,
            2: 1,
            4: 0xdb43306b16c521b9cc3667fbe7d1b697bb1f9605,
            5: 1,
            230: 0xdb43306b16c521b9cc3667fbe7d1b697bb1f9605,
            232: 0xebaf50debf10e08302fe4280c32df010463ca297,
            236: 64,
            238: 34,
            240: 10,
        },
            ),
        addr_0x1000000000000000000000000000000000000001: Account(storage={1: 0, 2: 0, 4: 0}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={4: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
