"""
test_create_empty_contract_with_storage

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractWithStorageFiller.json
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
    ["state_tests/stCreateTest/CREATE_EmptyContractWithStorageFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_empty_contract_with_storage(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """test_create_empty_contract_with_storage"""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
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

    pre[sender] = Account(balance=0xe8d4a51000)
    # Source: lll
    # { [[0]](GAS) (MSTORE 0 0x600c6000556000600060006000600073c94f5374fce5edbc8e2a8697c1533167) (MSTORE 32 0x7e6ebf0b61ea60f1000000000000000000000000000000000000000000000000) [[1]] (CREATE 0 0 64) [[100]] (GAS) }
    contract_0 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.MSTORE(offset=0x0, value=0x600c6000556000600060006000600073c94f5374fce5edbc8e2a8697c1533167)
        + Op.MSTORE(offset=0x20, value=0x7e6ebf0b61ea60f1000000000000000000000000000000000000000000000000)
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x0, size=0x40))
        + Op.SSTORE(key=0x64, value=Op.GAS) + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # {[[1]]12}
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x1, value=0xc) + Op.STOP,
        balance=0xe8d4a51000,
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )


    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b'',
        gas_limit=600000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(
                storage={
            0: 0x8d5b6,
            1: 0xf1ecf98489fa9ed60a664fc4998db699cfa39d40,
            100: 0x6f4f0,
        },
            ),
        Address("0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"): Account(nonce=1),  # noqa: E501
        contract_1: Account(storage={1: 12}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
