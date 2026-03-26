"""
test_create_name_registrator_oog_mem_expansion_oov

Ported from:
state_tests/stSystemOperationsTest/createNameRegistratorOOG_MemExpansionOOVFiller.json
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
    ["state_tests/stSystemOperationsTest/createNameRegistratorOOG_MemExpansionOOVFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_name_registrator_oog_mem_expansion_oov(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_name_registrator_oog_mem_expansion_oov"""
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
        gas_limit=1000000,
    )

    # Source: lll
    # { (MSTORE 0 0x601080600c6000396000f3006000355415600957005b60203560003555) [[ 0 ]] (CREATE 11000 3 0xffffffffffffffffffffff) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=0x601080600c6000396000f3006000355415600957005b60203560003555)
        + Op.SSTORE(key=0x0, value=Op.CREATE(value=0x2af8, offset=0x3, size=0xffffffffffffffffffffff))  # noqa: E501
        + Op.STOP,
        balance=10000,
        nonce=0,
        address=Address("0xb8d613d3333f8ce34bc851256b3096ffa7932f6e"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xde0b6b3a7640000)


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=300000,
        value=0x186a0,
        nonce=0,
        gas_price=10,
    )

    post = {target: Account(storage={}, nonce=0)}

    state_test(env=env, pre=pre, post=post, tx=tx)
