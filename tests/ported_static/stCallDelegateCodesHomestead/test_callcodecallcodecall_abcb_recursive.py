"""
DELEGATECALL -> DELEGATECALL2 -> CALL -> DELEGATECALL2 -> ...

Ported from:
tests/static/state_tests/stCallDelegateCodesHomestead
callcodecallcodecall_ABCB_RECURSIVEFiller.json
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
        "tests/static/state_tests/stCallDelegateCodesHomestead/callcodecallcodecall_ABCB_RECURSIVEFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcodecallcodecall_abcb_recursive(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """DELEGATECALL -> DELEGATECALL2 -> CALL -> DELEGATECALL2 -> ..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=3000000000,
    )

    # Source: LLL
    # {  [[ 0 ]] (DELEGATECALL 25000000 <contract:0x1000000000000000000000000000000000000001> 0 64 0 64 ) }  # noqa: E501
    contract = pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x0,
                value=Op.DELEGATECALL(
                    gas=0x17D7840,
                    address=0xE0B280638526CECD3EC29969B517AEB3FCBB31FA,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address("0x15600a91a7af84b8c85782714b3391ed5d73f9a0"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x2,
                value=Op.CALL(
                    gas=0x7A120,
                    address=0xE0B280638526CECD3EC29969B517AEB3FCBB31FA,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0x91a8703c1bef34c1e76e152c1f7fb8c336c3be24"),  # noqa: E501
    )
    pre.deploy_contract(
        code=(
            Op.SSTORE(
                key=0x1,
                value=Op.DELEGATECALL(
                    gas=0xF4240,
                    address=0x91A8703C1BEF34C1E76E152C1F7FB8C336C3BE24,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
        ),
        balance=0x2540BE400,
        nonce=0,
        address=Address("0xe0b280638526cecd3ec29969b517aeb3fcbb31fa"),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=contract,
        gas_limit=600000,
    )

    post = {
        contract: Account(storage={0: 1, 1: 1}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
