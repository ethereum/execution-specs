"""
Test_static_create_contract_suicide_during_init.

Ported from:
state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInitFiller.json
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
    compute_create_address,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stStaticCall/static_CREATE_ContractSuicideDuringInitFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.slow
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_static_create_contract_suicide_during_init(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_static_create_contract_suicide_during_init."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_1 = Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_2 = Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
    contract_3 = Address(0xE94F5374FCE5EDBC8E2A8697C15331677E6EBF0B)
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
    # { (MSTORE 1 1) }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address(0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        balance=11,
        nonce=0,
        address=Address(0xB94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (SSTORE 1 1) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x1, value=0x1) + Op.STOP,
        balance=11,
        nonce=0,
        address=Address(0xD94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )
    # Source: lll
    # { (CALL 100 0xc94f5374fce5edbc8e2a8697c15331677e6ebf0b 1 0 0 0 0) }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x64,
            address=0xC94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
            value=0x1,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=11,
        nonce=0,
        address=Address(0xE94F5374FCE5EDBC8E2A8697C15331677E6EBF0B),  # noqa: E501
    )

    tx_data = [
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_0),
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_1,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_0),
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_2,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_0),
        Op.POP(
            Op.STATICCALL(
                gas=0xEA60,
                address=contract_3,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
        )
        + Op.MSTORE(offset=0x0, value=0x64600C6000556000526005601BF3)
        + Op.SELFDESTRUCT(address=contract_0),
    ]
    tx_gas = [150000]

    tx = Transaction(
        sender=sender,
        to=None,
        data=tx_data[d],
        gas_limit=tx_gas[g],
    )

    post = {
        compute_create_address(address=sender, nonce=0): Account.NONEXISTENT,
        contract_0: Account(storage={1: 0}, balance=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
