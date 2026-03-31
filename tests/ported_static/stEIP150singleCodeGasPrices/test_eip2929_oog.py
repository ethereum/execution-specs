"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml
"""

import pytest
from execution_testing import (
    EOA,
    Account,
    Address,
    Alloc,
    Bytes,
    Environment,
    Hash,
    StateTestFiller,
    Transaction,
)
from execution_testing.forks import Fork
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            1,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            2,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            3,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            4,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            5,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            6,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            7,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            8,
            0,
            0,
            id="failEIP2929",
        ),
        pytest.param(
            9,
            0,
            0,
            id="failEIP2929",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_eip2929_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    coinbase = Address(0x2ADC25665018AA1FE0E6BC666DAC8FC2697FF9BA)
    contract_0 = Address(0x0000000000000000000000000000000000001054)
    contract_1 = Address(0x0000000000000000000000000000000000001055)
    contract_2 = Address(0x0000000000000000000000000000000000001031)
    contract_3 = Address(0x000000000000000000000000000000000000103B)
    contract_4 = Address(0x000000000000000000000000000000000000103C)
    contract_5 = Address(0x000000000000000000000000000000000000103F)
    contract_6 = Address(0x00000000000000000000000000000000000010F1)
    contract_7 = Address(0x00000000000000000000000000000000000010F2)
    contract_8 = Address(0x00000000000000000000000000000000000010F4)
    contract_9 = Address(0x00000000000000000000000000000000000010FA)
    contract_10 = Address(0x000000000000000000000000000000000000ACC7)
    contract_11 = Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC)
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    # Source: lll
    # {
    #    @@0
    # }
    contract_0 = pre.deploy_contract(  # noqa: F841
        code=Op.SLOAD(key=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000001054),  # noqa: E501
    )
    # Source: lll
    # {
    #    [[0]] 0x60A7
    # }
    contract_1 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(key=0x0, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000001055),  # noqa: E501
    )
    # Source: lll
    # {
    #    (balance 0xACC7)
    # }
    contract_2 = pre.deploy_contract(  # noqa: F841
        code=Op.BALANCE(address=0xACC7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0000000000000000000000000000000000001031),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodesize 0x1031)
    # }
    contract_3 = pre.deploy_contract(  # noqa: F841
        code=Op.EXTCODESIZE(address=0x1031) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000103B),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodecopy 0x1031 0 0 0x20)
    # }
    contract_4 = pre.deploy_contract(  # noqa: F841
        code=Op.EXTCODECOPY(
            address=0x1031, dest_offset=0x0, offset=0x0, size=0x20
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000103C),  # noqa: E501
    )
    # Source: lll
    # {
    #    (extcodehash 0x1031)
    # }
    contract_5 = pre.deploy_contract(  # noqa: F841
        code=Op.EXTCODEHASH(address=0x1031) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000103F),  # noqa: E501
    )
    # Source: lll
    # {
    #    (call 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_6 = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=0x6A5,
            address=0xACC7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000010F1),  # noqa: E501
    )
    # Source: lll
    # {
    #    (callcode 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_7 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=0x6A5,
            address=0xACC7,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000010F2),  # noqa: E501
    )
    # Source: lll
    # {
    #    (delegatecall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_8 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=0x6A5,
            address=0xACC7,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000010F4),  # noqa: E501
    )
    # Source: lll
    # {
    #    (staticcall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_9 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=0x6A5,
            address=0xACC7,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x00000000000000000000000000000000000010FA),  # noqa: E501
    )
    # Source: lll
    # {
    #    (return 0 0)
    # }
    contract_10 = pre.deploy_contract(  # noqa: F841
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x000000000000000000000000000000000000ACC7),  # noqa: E501
    )
    # Source: lll
    # {
    #    (def 'addr     $4)     ; the address to call
    #    (def 'callGas $36)     ; the amount of gas to give it
    #
    #    [[0]] (call callGas addr 0 0 0 0 0)
    # }
    contract_11 = pre.deploy_contract(  # noqa: F841
        code=Op.SSTORE(
            key=0x0,
            value=Op.CALL(
                gas=Op.CALLDATALOAD(offset=0x24),
                address=Op.CALLDATALOAD(offset=0x4),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            ),
        )
        + Op.STOP,
        storage={0: 24743},
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0xCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC),  # noqa: E501
    )
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)

    tx_data = [
        Bytes("1a8451e6") + Hash(contract_0, left_padding=True) + Hash(0x7D0),
        Bytes("1a8451e6") + Hash(contract_1, left_padding=True) + Hash(0x55F0),
        Bytes("1a8451e6") + Hash(contract_2, left_padding=True) + Hash(0x7D0),
        Bytes("1a8451e6") + Hash(contract_3, left_padding=True) + Hash(0x9C4),
        Bytes("1a8451e6") + Hash(contract_4, left_padding=True) + Hash(0x9C4),
        Bytes("1a8451e6") + Hash(contract_5, left_padding=True) + Hash(0x9C4),
        Bytes("1a8451e6") + Hash(contract_6, left_padding=True) + Hash(0x6D6),
        Bytes("1a8451e6") + Hash(contract_7, left_padding=True) + Hash(0x6D6),
        Bytes("1a8451e6") + Hash(contract_8, left_padding=True) + Hash(0x6D6),
        Bytes("1a8451e6") + Hash(contract_9, left_padding=True) + Hash(0x6D6),
    ]
    tx_gas = [16777216]
    tx_value = [1]

    tx = Transaction(
        sender=sender,
        to=contract_11,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        value=tx_value[v],
        nonce=1,
    )

    post = {contract_11: Account(storage={0: 0})}

    state_test(env=env, pre=pre, post=post, tx=tx)
