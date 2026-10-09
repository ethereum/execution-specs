"""
Ori Pomerantz qbzzt1@gmail.com.

Ported from:
state_tests/stEIP150singleCodeGasPrices/eip2929OOGFiller.yml

@manually-enhanced: Do not overwrite. EIP-7928 block access list
expectations added: a frame starved of its cold access cost leaves the
target account out of the list. The transaction's gas limit is exactly
`TX_MAX_GAS_LIMIT`, so its state gas reservoir is zero and no storage
can be created here; the SSTORE case therefore pins the implicit read,
not a write boundary.
"""

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    BalAccountExpectation,
    BlockAccessListExpectation,
    Bytes,
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
def test_eip2929_oog(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Ori Pomerantz qbzzt1@gmail."""
    sender = pre.fund_eoa(amount=0xBA1A9CE0BA1A9CE)
    # Source: lll
    # {
    #    @@0
    # }
    contract_0 = pre.deploy_contract(
        code=Op.SLOAD(key=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    [[0]] 0x60A7
    # }
    contract_1 = pre.deploy_contract(
        code=Op.SSTORE(key=0x0, value=0x60A7) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (return 0 0)
    # }
    contract_10 = pre.deploy_contract(
        code=Op.RETURN(offset=0x0, size=0x0) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (def 'addr     $4)     ; the address to call
    #    (def 'callGas $36)     ; the amount of gas to give it
    #
    #    [[0]] (call callGas addr 0 0 0 0 0)
    # }
    contract_11 = pre.deploy_contract(
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
    )
    # Source: lll
    # {
    #    (balance 0xACC7)
    # }
    contract_2 = pre.deploy_contract(
        code=Op.BALANCE(address=contract_10) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (call 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_6 = pre.deploy_contract(
        code=Op.CALL(
            gas=0x6A5,
            address=contract_10,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (staticcall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_9 = pre.deploy_contract(
        code=Op.STATICCALL(
            gas=0x6A5,
            address=contract_10,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (callcode 0x06A5 0xACC7 0 0 0 0 0)
    # }
    contract_7 = pre.deploy_contract(
        code=Op.CALLCODE(
            gas=0x6A5,
            address=contract_10,
            value=0x0,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (delegatecall 0x06A5 0xACC7 0 0 0 0)
    # }
    contract_8 = pre.deploy_contract(
        code=Op.DELEGATECALL(
            gas=0x6A5,
            address=contract_10,
            args_offset=0x0,
            args_size=0x0,
            ret_offset=0x0,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (extcodecopy 0x1031 0 0 0x20)
    # }
    contract_4 = pre.deploy_contract(
        code=Op.EXTCODECOPY(
            address=contract_2, dest_offset=0x0, offset=0x0, size=0x20
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (extcodesize 0x1031)
    # }
    contract_3 = pre.deploy_contract(
        code=Op.EXTCODESIZE(address=contract_2) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )
    # Source: lll
    # {
    #    (extcodehash 0x1031)
    # }
    contract_5 = pre.deploy_contract(
        code=Op.EXTCODEHASH(address=contract_2) + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
    )

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
    )

    post = {contract_11: Account(storage={0: 0})}

    expected_block_access_list = None
    if fork.is_eip_enabled(7928):
        # Each starved frame halts at its cold access charge, so the
        # account it reaches for never enters the block access list.
        # SSTORE is the exception: it pays the slot's access cost before
        # its implicit read, so the slot lands in `storage_reads`, and
        # the write cannot be recorded either way because this
        # transaction has no state gas to create storage with.
        expectations: dict[Address, BalAccountExpectation | None]
        if d == 0:  # SLOAD
            expectations = {contract_0: BalAccountExpectation.empty()}
        elif d == 1:  # SSTORE
            expectations = {
                contract_1: BalAccountExpectation(
                    storage_reads=[0], storage_changes=[]
                )
            }
        elif d == 2:  # BALANCE
            expectations = {
                contract_2: BalAccountExpectation.empty(),
                contract_10: None,
            }
        elif d == 3:  # EXTCODESIZE
            expectations = {
                contract_3: BalAccountExpectation.empty(),
                contract_2: None,
            }
        elif d == 4:  # EXTCODECOPY
            expectations = {
                contract_4: BalAccountExpectation.empty(),
                contract_2: None,
            }
        elif d == 5:  # EXTCODEHASH
            expectations = {
                contract_5: BalAccountExpectation.empty(),
                contract_2: None,
            }
        elif d == 6:  # CALL
            expectations = {
                contract_6: BalAccountExpectation.empty(),
                contract_10: None,
            }
        elif d == 7:  # CALLCODE
            expectations = {
                contract_7: BalAccountExpectation.empty(),
                contract_10: None,
            }
        elif d == 8:  # DELEGATECALL
            expectations = {
                contract_8: BalAccountExpectation.empty(),
                contract_10: None,
            }
        elif d == 9:  # STATICCALL
            expectations = {
                contract_9: BalAccountExpectation.empty(),
                contract_10: None,
            }
        else:
            raise ValueError(f"unhandled case: d={d}")
        expected_block_access_list = BlockAccessListExpectation(
            account_expectations=expectations
        )

    state_test(
        pre=pre,
        post=post,
        tx=tx,
        expected_block_access_list=expected_block_access_list,
    )
