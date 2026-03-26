"""
CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json
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
    ["state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecallcode_011_OOGMBeforeFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecallcode_011_oogm_before(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """CALLCODE -> DELEGATE -> OOG DELEGATE -> CODE"""
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
    # {  [[ 0 ]] (CALLCODE 150000 <contract:0x1000000000000000000000000000000000000001> 0 0 64 0 64 ) }
    target = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.CALLCODE(gas=0x249f0, address=0xb5104f0f7758ce0caac73f593c6d63eb9a5ef905, value=0x0, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        balance=0xde0b6b3a7640000,
        nonce=0,
        address=Address("0xa74ca10b765dcda3b60687f73f2881e2a56eda64"),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 40080 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) [[11]] 1 }
    addr_0x1000000000000000000000000000000000000001 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=Op.DELEGATECALL(gas=0x9c90, address=0xc176d297ff74c0f684b73d6cc8617e7f5ffe34fe, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.SSTORE(key=0xb, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb5104f0f7758ce0caac73f593c6d63eb9a5ef905"),  # noqa: E501
    )
    # Source: lll
    # {  (KECCAK256 0x00 0x2fffff) [[ 2 ]] (DELEGATECALL 20020 <contract:0x1000000000000000000000000000000000000003> 0 64 0 64 ) }
    addr_0x1000000000000000000000000000000000000002 = pre.deploy_contract(
        code=Op.POP(Op.SHA3(offset=0x0, size=0x2fffff))
        + Op.SSTORE(key=0x2, value=Op.DELEGATECALL(gas=0x4e34, address=0xb126c622075b1189fb6c45e851641cfaddf65b36, args_offset=0x0, args_size=0x40, ret_offset=0x0, ret_size=0x40))  # noqa: E501
        + Op.STOP,
        nonce=0,
        address=Address("0xc176d297ff74c0f684b73d6cc8617e7f5ffe34fe"),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) }
    addr_0x1000000000000000000000000000000000000003 = pre.deploy_contract(
        code=Op.SSTORE(key=0x3, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0xb126c622075b1189fb6c45e851641cfaddf65b36"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=172000,
        nonce=0,
        gas_price=10,
    )

    post = {
        target: Account(storage={0: 1, 11: 1}),
        addr_0x1000000000000000000000000000000000000001: Account(storage={}),
        addr_0x1000000000000000000000000000000000000002: Account(storage={}),
        addr_0x1000000000000000000000000000000000000003: Account(storage={}),
        sender: Account(storage={}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
