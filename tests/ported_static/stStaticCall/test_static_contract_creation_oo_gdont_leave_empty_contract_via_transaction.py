"""
Test_static_contract_creation_oo_gdont_leave_empty_contract_via_transact...

Ported from:
state_tests/stStaticCall/static_contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json
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
        "state_tests/stStaticCall/static_contractCreationOOGdontLeaveEmptyContractViaTransactionFiller.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_static_contract_creation_oo_gdont_leave_empty_contract_via_transaction(  # noqa: E501
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_static_contract_creation_oo_gdont_leave_empty_contract_via_tra..."""  # noqa: E501
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b")
    contract_1 = Address("0x1000000000000000000000000000000000000001")
    contract_2 = Address("0x2000000000000000000000000000000000000001")
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
        gas_limit=1000000,
    )

    pre[sender] = Account(balance=0x10C8E0)
    # Source: lll
    # {(STATICCALL 50000 0x1000000000000000000000000000000000000001 0 64 0 64)}
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0xC350,
            address=0x1000000000000000000000000000000000000001,
            args_offset=0x0,
            args_size=0x40,
            ret_offset=0x0,
            ret_size=0x40,
        )
        + Op.STOP,
        balance=0x186A0,
        nonce=0,
        address=Address("0xb94f5374fce5edbc8e2a8697c15331677e6ebf0b"),  # noqa: E501
    )
    # Source: lll
    # {(MSTORE 1 1)}
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.MSTORE(offset=0x1, value=0x1) + Op.STOP,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000001"),  # noqa: E501
    )
    # Source: lll
    # { (def 'i 0x80) (for {} (< @i 50000) [i](+ @i 1) (EXTCODESIZE 1)) }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.JUMPDEST
        + Op.JUMPI(
            pc=0x1C, condition=Op.ISZERO(Op.LT(Op.MLOAD(offset=0x80), 0xC350))
        )
        + Op.POP(Op.EXTCODESIZE(address=0x1))
        + Op.MSTORE(offset=0x80, value=Op.ADD(Op.MLOAD(offset=0x80), 0x1))
        + Op.JUMP(pc=0x0)
        + Op.JUMPDEST
        + Op.STOP,
        nonce=0,
        address=Address("0x2000000000000000000000000000000000000001"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "604060006040600073200000000000000000000000000000000000000161c350fa"  # noqa: E501
        ),
        gas_limit=96000,
        nonce=0,
        gas_price=10,
    )

    post = {
        Address("0x6295ee1b4f6dd65047762f924ecd367c17eabf8f"): Account(
            nonce=1
        ),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
