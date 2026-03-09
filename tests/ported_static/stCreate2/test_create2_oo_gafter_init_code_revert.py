"""
Calls a contract that runs CREATE2 which deploy a code. then after...

Ported from:
tests/static/state_tests/stCreate2/Create2OOGafterInitCodeRevertFiller.json
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
    [
        "tests/static/state_tests/stCreate2/Create2OOGafterInitCodeRevertFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_create2_oo_gafter_init_code_revert(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Calls a contract that runs CREATE2 which deploy a code. then..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
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
    # Source: LLL
    # { (MSTORE 0 0x6460016001556000526005601bf3) (CREATE2 0 18 14 0) (REVERT 0 32) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=0x6460016001556000526005601BF3)
            + Op.POP(Op.CREATE2(value=0x0, offset=0x12, size=0xE, salt=0x0))
            + Op.REVERT(offset=0x0, size=0x20)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL (GAS) 0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b 0 0 0 0 32) [[ 1 ]] (MLOAD 0) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.POP(
                Op.CALL(
                    gas=Op.GAS,
                    address=0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x20,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.MLOAD(offset=0x0))
            + Op.STOP
        ),
        storage={0x1: 0x1},
        nonce=0,
        address=Address("0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=75000,
    )

    post = {
        contract: Account(storage={1: 0x6460016001556000526005601BF3}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
