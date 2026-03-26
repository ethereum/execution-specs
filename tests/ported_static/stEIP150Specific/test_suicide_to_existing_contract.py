"""
test_suicide_to_existing_contract

Ported from:
state_tests/stEIP150Specific/SuicideToExistingContractFiller.json
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
    ["state_tests/stEIP150Specific/SuicideToExistingContractFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_suicide_to_existing_contract"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4f31b3206fbf0e0e598b9b1a7d8ac86302a0ff1d8930738f1bebae9b67173e52
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }
    target = pre.deploy_contract(
        code=Op.MSTORE(offset=0x0, value=Op.GAS)
        + Op.POP(Op.CALL(gas=0xea60, address=0x79968a94dbedb20475585e9dd4dae6333add4c01, value=0x0, args_offset=0x0, args_size=0x0, ret_offset=0x0, ret_size=0x0))
        + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
        + Op.STOP,
        nonce=0,
        address=Address("0xe110d543aadc3060d6b9e80d3e16be7a828128ec"),  # noqa: E501
    )
    # Source: lll
    # { (SELFDESTRUCT <contract:target:0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b>) }
    addr_0x1000000000000000000000000000000000000118 = pre.deploy_contract(
        code=Op.SELFDESTRUCT(address=0xe110d543aadc3060d6b9e80d3e16be7a828128ec)
        + Op.STOP,
        nonce=0,
        address=Address("0x79968a94dbedb20475585e9dd4dae6333add4c01"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=target,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        addr_0x1000000000000000000000000000000000000118: Account(
                storage={},
                code=bytes.fromhex("73e110d543aadc3060d6b9e80d3e16be7a828128ecff00"),  # noqa: E501
                balance=0,
                nonce=0,
            ),
        target: Account(storage={1: 7637}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
