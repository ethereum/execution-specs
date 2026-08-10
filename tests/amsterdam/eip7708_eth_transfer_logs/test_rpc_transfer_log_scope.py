"""
Tests that pin which ETH movements EIP-7708 logs, over JSON-RPC.

EIP-7708's specification is a closed list: a Transfer log is issued for a
nonzero-value-transferring transaction, `CALL`, or `SELFDESTRUCT` to a
different account, and for a nonzero-value-transferring `CREATE` or
`CREATE2` to the created account. Nothing else. The movements it leaves
out — a zero-value transfer, the priority fee paid to the coinbase, the
base fee burn, and a withdrawal — move ETH just as visibly, and the
rationale turns each of them down by name.

That boundary is the entire content of the EIP for anyone deriving a
transfer list from logs, and it is about to be compared against a second
one. `eth_simulateV1`'s `traceTransfers` synthesizes the same
ERC-20-shaped log for ETH movements it observes, from a different
emitter, over a scope neither specification states. No client implements
both, so the two scopes have never had to agree. These tests write down
the EIP-7708 half, so that the comparison has something to be made
against.

Every exclusion here is asserted against a block that also contains a
movement the EIP does log. The pairing is not incidental. A filtered
`eth_getLogs` result is compared entry by entry, so the included transfer
fixes both the contents and the length of the list, and a client that
adds an entry for the excluded movement fails on length before any value
is examined. An empty expectation would assert far less, and cannot be
stored at all: the method's OpenRPC result schema is a `oneOf` that an
empty array satisfies twice over.
"""

from typing import Any, Dict, List

import pytest
from execution_testing import (
    Account,
    Address,
    Alloc,
    Block,
    BlockchainTestFiller,
    Op,
    Transaction,
    TransactionReceipt,
    Withdrawal,
    compute_create_address,
)
from execution_testing.specs.blockchain import RPCExpectation

from .spec import Spec, ref_spec_7708, transfer_log

REFERENCE_SPEC_GIT_PATH = ref_spec_7708.git_path
REFERENCE_SPEC_VERSION = ref_spec_7708.version

pytestmark = [pytest.mark.valid_from("EIP7708"), pytest.mark.rpc]


def transfer_log_query(last_block: int) -> RPCExpectation:
    """
    Return the query for every EIP-7708 Transfer log up to `last_block`.

    Filtering on the emitter and the event signature asks the chain
    exactly the question this EIP exists to answer, and the same one a
    `traceTransfers` consumer asks: list the ETH movements. The answer is
    derived from the chain rather than written here, so what the test
    contributes is the question and the completeness of the reply — a
    client that reports a movement the EIP excludes has a longer list
    than the specification computed, whatever the extra entry says.

    The range is named by number because a block tag resolves against
    client state rather than against the chain, and derivation refuses to
    guess at one.
    """
    return RPCExpectation(
        method="eth_getLogs",
        params=[
            {
                "fromBlock": "0x0",
                "toBlock": hex(last_block),
                "address": str(Spec.SYSTEM_ADDRESS),
                "topics": [str(Spec.TRANSFER_TOPIC)],
            }
        ],
        derive_result=True,
    )


def test_rpc_logs_a_transaction_transfer(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A nonzero-value transaction between two distinct accounts.

    The first entry on the EIP's list, and the control the exclusions are
    measured against: whatever else a client reports, it must report this.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    amount = 10**9

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=recipient,
                        value=amount,
                        expected_receipt=TransactionReceipt(
                            logs=[transfer_log(sender, recipient, amount)]
                        ),
                    )
                ]
            )
        ],
        post={recipient: Account(balance=amount)},
        rpc_checks=[transfer_log_query(1)],
    )


def test_rpc_logs_a_call_transfer(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A nonzero-value `CALL` to a different account.

    Two logs, not one: the transaction endows the caller and the caller
    forwards to the callee, and both are on the EIP's list. Their order is
    the order the transfers executed.
    """
    callee = pre.deploy_contract(Op.STOP)
    forwarded = 10**9
    caller = pre.deploy_contract(
        Op.CALL(address=callee, value=forwarded), balance=forwarded
    )
    sender = pre.fund_eoa()
    endowment = 10**9

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=caller,
                        value=endowment,
                        expected_receipt=TransactionReceipt(
                            logs=[
                                transfer_log(sender, caller, endowment),
                                transfer_log(caller, callee, forwarded),
                            ]
                        ),
                    )
                ]
            )
        ],
        post={callee: Account(balance=forwarded)},
        rpc_checks=[transfer_log_query(1)],
    )


def test_rpc_logs_a_selfdestruct_transfer(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A nonzero-value `SELFDESTRUCT` to a different account.

    The beneficiary is a fresh account, so the swept balance is the whole
    of the movement and the logged amount has nothing else mixed into it.
    """
    beneficiary = pre.fund_eoa(amount=0)
    swept = 10**9
    contract = pre.deploy_contract(
        Op.SELFDESTRUCT(beneficiary), balance=swept
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=contract,
                        value=0,
                        expected_receipt=TransactionReceipt(
                            logs=[
                                transfer_log(contract, beneficiary, swept)
                            ]
                        ),
                    )
                ]
            )
        ],
        post={beneficiary: Account(balance=swept)},
        rpc_checks=[transfer_log_query(1)],
    )


@pytest.mark.with_all_create_opcodes
def test_rpc_logs_a_create_endowment(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
    create_opcode: Op,
) -> None:
    """
    A nonzero-value `CREATE` or `CREATE2` endowment to the created account.

    The recipient is an account that did not exist when the transaction
    started, which is what separates this bullet of the EIP from the
    `CALL` one: the log names an address the chain has only just decided
    on.
    """
    initcode = Op.RETURN(0, 0)
    initcode_length = len(initcode)
    endowment = 10**9

    factory_code = Op.MSTORE(
        0, Op.PUSH32(bytes(initcode).rjust(32, b"\x00"))
    ) + create_opcode(
        value=endowment,
        offset=32 - initcode_length,
        size=initcode_length,
    )
    factory = pre.deploy_contract(factory_code, balance=endowment)
    created = compute_create_address(
        address=factory,
        nonce=1,
        salt=0,
        initcode=initcode,
        opcode=create_opcode,
    )
    sender = pre.fund_eoa()

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=factory,
                        value=0,
                        expected_receipt=TransactionReceipt(
                            logs=[
                                transfer_log(factory, created, endowment)
                            ]
                        ),
                    )
                ]
            )
        ],
        post={created: Account(balance=endowment)},
        rpc_checks=[transfer_log_query(1)],
    )


def test_rpc_omits_a_zero_value_transfer(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    A zero-value transfer, alongside a nonzero one that is logged.

    "Nonzero-value-transferring" is a condition on all four bullets of the
    EIP, and a zero-value transaction is otherwise indistinguishable from
    a logged one — same shape, same recipient, same execution path — so a
    client emitting on the movement rather than on its amount fails only
    here.
    """
    sender = pre.fund_eoa()
    recipient = pre.fund_eoa(amount=0)
    amount = 10**9

    blockchain_test(
        pre=pre,
        blocks=[
            Block(
                txs=[
                    Transaction(
                        sender=sender,
                        to=recipient,
                        value=0,
                        expected_receipt=TransactionReceipt(logs=[]),
                    ),
                    Transaction(
                        sender=sender,
                        to=recipient,
                        value=amount,
                        expected_receipt=TransactionReceipt(
                            logs=[transfer_log(sender, recipient, amount)]
                        ),
                    ),
                ]
            )
        ],
        post={recipient: Account(balance=amount)},
        rpc_checks=[transfer_log_query(1)],
    )
