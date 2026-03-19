"""
Test ported from static filler.

Ported from:
tests/static/state_tests/stEIP150Specific/SuicideToExistingContractFiller.json
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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stEIP150Specific/SuicideToExistingContractFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_suicide_to_existing_contract(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
) -> None:
    """Test ported from static filler."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x4F31B3206FBF0E0E598B9B1A7D8AC86302A0FF1D8930738F1BEBAE9B67173E52
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    callee = pre.deploy_contract(
        code=(
            Op.SELFDESTRUCT(address=0xE110D543AADC3060D6B9E80D3E16BE7A828128EC)
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x79968a94dbedb20475585e9dd4dae6333add4c01"),  # noqa: E501
    )
    # Source: LLL
    # { [0] (GAS) (CALL 60000 <contract:0x1000000000000000000000000000000000000118> 0 0 0 0 0) [[1]] (SUB @0 (GAS)) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.MSTORE(offset=0x0, value=Op.GAS)
            + Op.POP(
                Op.CALL(
                    gas=0xEA60,
                    address=0x79968A94DBEDB20475585E9DD4DAE6333ADD4C01,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x0,
                    ret_offset=0x0,
                    ret_size=0x0,
                ),
            )
            + Op.SSTORE(key=0x1, value=Op.SUB(Op.MLOAD(offset=0x0), Op.GAS))
            + Op.STOP
        ),
        nonce=0,
        address=Address("0xe110d543aadc3060d6b9e80d3e16be7a828128ec"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xE8D4A51000)

    EXPECT_ENTRIES: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "73e110d543aadc3060d6b9e80d3e16be7a828128ecff00"
                    )
                ),
                contract: Account(
                    storage={1: 7637},
                    code=bytes.fromhex(
                        "5a600052600060006000600060007379968a94dbedb20475585e9dd4dae6333add4c0161ea60f1505a6000510360015500"  # noqa: E501
                    ),
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(EXPECT_ENTRIES, 0, 0, 0, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
