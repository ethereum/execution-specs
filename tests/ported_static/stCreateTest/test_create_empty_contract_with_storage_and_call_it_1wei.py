"""
Test_create_empty_contract_with_storage_and_call_it_1wei.

Ported from:
state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_1weiFiller.json
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
    compute_create_address,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCreateTest/CREATE_EmptyContractWithStorageAndCallIt_1weiFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create_empty_contract_with_storage_and_call_it_1wei(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_create_empty_contract_with_storage_and_call_it_1wei."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { [[0]](GAS) (MSTORE 0 0x600c6000556000600060006000600073c94f5374fce5edbc8e2a8697c1533167) (MSTORE 32 0x7e6ebf0b61ea60f1000000000000000000000000000000000000000000000000) [[1]] (CREATE 0 0 64) [[2]] (GAS) [[3]] (CALL 60000 (SLOAD 1) 1 0 0 0 0) [[100]] (GAS) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=Op.GAS)
        + Op.MSTORE(
            offset=0x0,
            value=0x600C6000556000600060006000600073C94F5374FCE5EDBC8E2A8697C1533167,  # noqa: E501
        )
        + Op.MSTORE(
            offset=0x20,
            value=0x7E6EBF0B61EA60F1000000000000000000000000000000000000000000000000,  # noqa: E501
        )
        + Op.SSTORE(key=0x1, value=Op.CREATE(value=0x0, offset=0x0, size=0x40))
        + Op.SSTORE(key=0x2, value=Op.GAS)
        + Op.SSTORE(
            key=0x3,
            value=Op.CALL(
                gas=0xEA60,
                address=Op.SLOAD(key=0x1),
                value=0x1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.SSTORE(key=0x64, value=Op.GAS)
        + Op.STOP,
        balance=1,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # {[[1]]12}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0xC) + Op.STOP,
        balance=0xE8D4A51000,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=Bytes(""),
        gas_limit=600000,
    )

    post = {
        contract_0: Account(
            storage={
                0: 0x8D5B6,
                1: 0xF1ECF98489FA9ED60A664FC4998DB699CFA39D40,
                2: 0x6F4F0,
                3: 1,
                100: 0x62D37,
            },
        ),
        compute_create_address(address=contract_0, nonce=0): Account(
            storage={0: 12}, balance=1
        ),
        contract_1: Account(storage={1: 12}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
