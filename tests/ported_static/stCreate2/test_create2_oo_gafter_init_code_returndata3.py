"""
Calls a contract that runs CREATE2 which deploy a code. then OOG...

Ported from:
state_tests/stCreate2/Create2OOGafterInitCodeReturndata3Filler.json
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
    ["state_tests/stCreate2/Create2OOGafterInitCodeReturndata3Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_oo_gafter_init_code_returndata3(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE2 which deploy a code."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
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

    pre[sender] = Account(balance=0xE8D4A51000)
    # Source: lll
    # { (CALLCODE (GAS) 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) (RETURNDATACOPY 0 0 32) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.POP(
            Op.CALLCODE(
                gas=Op.GAS,
                address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x20,
            )
        )
        + Op.RETURNDATACOPY(dest_offset=0x0, offset=0x0, size=0x20)
        + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
        + Op.STOP,
        storage={1: 1},
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE2 0 18 14 0) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
        + Op.CREATE2(value=0x0, offset=0x12, size=0xE, salt=0x0)
        + Op.STOP,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract_0,
        data=b"",
        gas_limit=55000,
        nonce=0,
        gas_price=10,
    )

    post = {
        contract_0: Account(storage={1: 1}),
        Address(
            "0xf1ecf98489fa9ed60a664fc4998db699cfa39d40"
        ): Account.NONEXISTENT,
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
