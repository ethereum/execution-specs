"""
Test_callcallcodecall_010.

Ported from:
state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json
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
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    [
        "state_tests/stCallDelegateCodesCallCodeHomestead/callcallcodecall_010Filler.json"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_callcallcodecall_010(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_callcallcodecall_010."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    sender = EOA(
        key=0xE04D1AC7DDDA0C98397D56A0B501E960D4CD325A39286919AC23C1A07009A869
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=30000000,
    )

    # Source: lll
    # {  [[ 0 ]] (CALLCODE 350000 <contract:0x1000000000000000000000000000000000000001> 1 0 64 0 64 ) }  # noqa: E501
    target = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALLCODE(
                gas=0x55730,
                address=0xFED08E44AE95ECE264BC94A1FC45AF8BC4EF4F1D,
                value=0x1,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xDB43306B16C521B9CC3667FBE7D1B697BB1F9605),  # noqa: E501
    )
    # Source: lll
    # {  [[ 1 ]] (DELEGATECALL 300000 <contract:0x1000000000000000000000000000000000000002> 0 64 0 64 ) }  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x1,
            value=Op.DELEGATECALL(
                gas=0x493E0,
                address=0x8738AB5302009E8BAD163C8A9E91E72926B09D34,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0xFED08E44AE95ECE264BC94A1FC45AF8BC4EF4F1D),  # noqa: E501
    )
    # Source: lll
    # {  [[ 2 ]] (CALLCODE 250000 <contract:0x1000000000000000000000000000000000000003> 2 0 64 0 64 ) (SSTORE 5 (CALLER))}  # noqa: E501
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x2,
            value=Op.CALLCODE(
                gas=0x3D090,
                address=0xB8601B04BFD9EB63BC6FF0263567113D4CB874E4,
                value=0x2,
                args_offset=0x0,
                args_size=0x40,
                ret_offset=0x0,
                ret_size=0x40,
            ),
        )
        + Op.SSTORE(key=0x5, value=Op.CALLER)
        + Op.STOP,
        balance=0xDE0B6B3A7640000,
        nonce=0,
        address=Address(0x8738AB5302009E8BAD163C8A9E91E72926B09D34),  # noqa: E501
    )
    # Source: lll
    # {  (SSTORE 3 1) (SSTORE 4 (CALLER)) (SSTORE 6 (CALLVALUE)) (SSTORE 330 (ADDRESS)) (SSTORE 332 (ORIGIN)) (SSTORE 336 (CALLDATASIZE)) (SSTORE 338 (CODESIZE)) (SSTORE 340 (GASPRICE))}  # noqa: E501
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x3, value=0x1)
        + Op.SSTORE(key=0x4, value=Op.CALLER)
        + Op.SSTORE(key=0x6, value=Op.CALLVALUE)
        + Op.SSTORE(key=0x14A, value=Op.ADDRESS)
        + Op.SSTORE(key=0x14C, value=Op.ORIGIN)
        + Op.SSTORE(key=0x150, value=Op.CALLDATASIZE)
        + Op.SSTORE(key=0x152, value=Op.CODESIZE)
        + Op.SSTORE(key=0x154, value=Op.GASPRICE)
        + Op.STOP,
        nonce=0,
        address=Address(0xB8601B04BFD9EB63BC6FF0263567113D4CB874E4),  # noqa: E501
    )
    pre[sender] = Account(balance=0xDE0B6B3A7640000)

    tx = Transaction(
        sender=sender,
        to=target,
        data=Bytes(""),
        gas_limit=3000000,
    )

    post = {
        target: Account(
            storage={
                0: 1,
                1: 1,
                2: 1,
                3: 1,
                4: 0xDB43306B16C521B9CC3667FBE7D1B697BB1F9605,
                5: 0xDB43306B16C521B9CC3667FBE7D1B697BB1F9605,
                6: 2,
                330: 0xDB43306B16C521B9CC3667FBE7D1B697BB1F9605,
                332: 0xEBAF50DEBF10E08302FE4280C32DF010463CA297,
                336: 64,
                338: 39,
                340: 10,
            },
        ),
        addr: Account(storage={1: 0, 2: 0, 5: 0}),
        addr_2: Account(storage={2: 0}),
        addr_3: Account(storage={3: 0, 4: 0}),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
