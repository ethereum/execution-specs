"""
abstract: Tests practical scenarios on Mainnet with the XEN (which has a big state) contract

Tests practical scenarios on Mainnet with the XEN (which has a big state) contract.
This currently has one situation, but will be expanded with other scenarios.
The goal is to bloat as much of the big state of XEN as possible. XEN has a big state trie.
We therefore want to do as much state situations (either read or write: likely write is
the most expensive situation).
NOTE: this is thus NOT the worst-case scenario, since we can remove the overhead execution
computations for XEN and only do state operations on an account with a big state attached to it.
This therefore only tests the practical, "real life" and most likely scenario.
However, with enough funds (to bloat a contract state), this is thus not the worst scenario.
"""

import pytest

from ethereum_test_forks import Fork
from ethereum_test_tools import (
    Account,
    Alloc,
    Block,
    BlockchainTestFiller,
    Environment,
    Hash,
    Transaction,
    While,
)
from ethereum_test_tools import Macros as Om
from ethereum_test_vm import Opcodes as Op

# TODO
# Modularize each test, there is too much duplicated code now
# Identify more scenarios
# Rewrite tests to support the gas benchmark target
# Check if some helper methods or contract patterns should be extracted for further mainnet use
# for other target contracts (such as ERC20 contracts).


@pytest.mark.valid_from("Frontier")
def test_xen_read_balance_nonexisting(blockchain_test: BlockchainTestFiller, pre: Alloc) -> None:
    """
    Reads balanceOf(address) starting from the index specified in the first 32 bytes of the
    tx calldata (0 if no calldata provided) and keeps reading balanceOf(address) where this
    address is incremented by one each loop. The tx will OOG, as only state reads and
    no state writes are relevant in this scenario.
    This test attempts to read as many non-existent storage slots as possible.
    """
    attack_gas_limit = (
        60_000_000  # TODO: currently hardcoded, should be read from `gas_benchmark_value`
    )
    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8

    fn_signature_balance_of = bytes.fromhex(
        "70A08231"
    )  # Function selector of `balanceOf(address)`
    # The code below will OOG and will keep incrementing the address read by one each time
    # The start address can be set in the first 32 bytes of the calldata
    # NOTE: empty calldata thus starts at address 0
    balance_of_loop = (
        Om.MSTORE(fn_signature_balance_of)
        + Op.MSTORE(4, Op.CALLDATALOAD(0))
        + Op.CALLDATALOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=xen_contract, args_offset=0, args_size=4 + 32)
            + Op.ADD,  # Add the status of the CALL
        )
    )

    approval_spammer_contract = pre.deploy_contract(code=balance_of_loop)

    attack_tx = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit,
        # data=calldata, Use empty calldata, start at address 0
        # NOTE: if different storage slots have to be read across different transactions
        # then calldata has to be used to set the correct start addresses
        sender=pre.fund_eoa(),
    )

    blocks = [Block(txs=[attack_tx])]

    blockchain_test(
        pre=pre,
        post={},
        blocks=blocks,
        skip_gas_used_validation=True,
    )


# TODO: add test which writes to already existing storage
@pytest.mark.valid_from("Frontier")
def test_xen_approve_set_only(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Uses the `approve(address,uint256)` method of XEN (ERC20) close to the maximum amount
    of new slots which could be created within a single block/transaction.
    """
    attack_gas_limit = (
        60_000_000  # TODO: currently hardcoded, should be read from `gas_benchmark_value`
    )

    # Gas limit: 60M, 2424 SSTOREs, 300 MGas/s

    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8
    gas_threshold = 40_000

    fn_signature_approve = bytes.fromhex(
        "095EA7B3"
    )  # Function selector of `approve(address,uint256)`
    # This code loops until there is less than threshold_gas left and reads two items from calldata:
    # The first 32 bytes are interpreted as the start address to start approving for
    # The second 32 bytes is the approval amount
    # This can thus be used to initialize the approvals (in multiple txs) to write to the storage
    # Since initializing storage (from zero to nonzero) is more expensive, this thus has
    # to be done over multiple blocks/txs
    # The attack block can then target all of the just initialized storage slots to edit
    # (This should thus yield more dirty trie nodes than the )
    approval_loop_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, Op.CALLDATALOAD(32))
        + Op.CALLDATALOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=xen_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            condition=Op.GT(Op.GAS, gas_threshold),
        )
    )

    approval_spammer_contract = pre.deploy_contract(code=approval_loop_code)

    start_address = Hash(0x01)  # Approvals to the zero address are rejected, so start at 1
    approval_value = Hash(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)

    calldata = start_address + approval_value

    attack_tx = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit,
        data=calldata,
        sender=pre.fund_eoa(),
    )

    blocks = [Block(txs=[attack_tx])]

    blockchain_test(
        pre=pre,
        post={},  # TODO: add sanity checks (succesful tx execution and no out-of-gas)
        blocks=blocks,
        skip_gas_used_validation=True,
    )


@pytest.mark.valid_from("Frontier")
def test_xen_approve_change_existing_slots(
    blockchain_test: BlockchainTestFiller,
    pre: Alloc,
) -> None:
    """
    Uses the `approve(address,uint256)` method of XEN (ERC20) close to the maximum amount
    of slots which could be edited (as opposed to be created) within a single block/transaction.
    """
    attack_gas_limit = (
        60_000_000  # TODO: currently hardcoded, should be read from `gas_benchmark_value`
    )

    # 22 Sep 10:08:22 | Processed            23366464         |      207.4 ms  | slot          1,734 ms |⛽ Gas gwei: 1.00 .. 1.00 (1.00) .. 1.00
    # 22 Sep 10:08:22 | Cleared caches: Rlp
    # 22 Sep 10:08:22 |  Block    0.0600 ETH    59.96 MGas    |        1   txs | calls      7,752 (  0) | sload       8 | sstore  7,762 | create   0
    # 22 Sep 10:08:22 |  Block throughput      289.05 MGas/s  |        4.8 tps |             4.82 Blk/s | exec code cache  15,508 | new      0 | ops   1,868,419

    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8
    gas_threshold = 40_000

    # This test deletes 9599 storage slots from XEN

    fn_signature_approve = bytes.fromhex(
        "095EA7B3"
    )  # Function selector of `approve(address,uint256)`
    # This code loops until there is less than threshold_gas left and reads two items from calldata:
    # The first 32 bytes are interpreted as the start address to start approving for
    # The second 32 bytes is the approval amount
    # This can thus be used to initialize the approvals (in multiple txs) to write to the storage
    # Since initializing storage (from zero to nonzero) is more expensive, this thus has
    # to be done over multiple blocks/txs
    # The attack block can then target all of the just initialized storage slots to edit
    # (This should thus yield more dirty trie nodes than the )
    approval_loop_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, Op.CALLDATALOAD(32))
        + Op.CALLDATALOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=xen_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 32), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
    )

    approval_spammer_contract = pre.deploy_contract(code=approval_loop_code)

    sender = pre.fund_eoa()

    blocks = []

    # TODO: calculate these constants based on the gas limit of the benchmark test
    start_address = 0x01  # XEN blocks approving the zero address
    current_address = start_address
    address_incr = 2000

    approval_value_fresh = Hash(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)
    approval_value_overwrite = Hash(0)

    block_count = 10

    for _ in range(block_count):
        setup_calldata = Hash(current_address) + approval_value_fresh
        setup_tx = Transaction(
            to=approval_spammer_contract,
            gas_limit=attack_gas_limit,
            data=setup_calldata,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[setup_tx]))

        current_address += address_incr

    fn_signature_approve = bytes.fromhex("095EA7B3")
    usdt_contract = 0xDAC17F958D2EE523A2206206994597C13D831EC7  # Used in intermediate blocks to attempt to bust te cache
    usdt_approve_spammer_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, 1)
        + Op.SLOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=usdt_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            # + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 34), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.PUSH1(0)
        + Op.SSTORE
    )
    # Set storage to value 1 to avoid paying 20k on the update
    usdt_approve_spammer_contract = pre.deploy_contract(
        code=usdt_approve_spammer_code, storage={0: 1}
    )

    spam_count = 200

    for _ in range(spam_count):
        # NOTE: USDC does not allow changing the approval value. It first has to be
        # set to zero before it changes. We therefore flood USDC with approvals in an
        # attempt to bust the cache
        spam_tx = Transaction(
            to=usdt_approve_spammer_contract,
            gas_limit=attack_gas_limit // 2,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[spam_tx]))

    attack_calldata = Hash(start_address) + approval_value_overwrite

    attack_tx = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit,
        max_priority_fee_per_gas=100,
        max_fee_per_gas=10000,
        data=attack_calldata,
        sender=sender,
    )
    blocks.append(Block(txs=[attack_tx]))

    blockchain_test(
        pre=pre,
        post={},  # TODO: add sanity checks (succesful tx execution and no out-of-gas)
        blocks=blocks,
        skip_gas_used_validation=True,
    )


# TODO split this code in all situations: 0->1, 1->2, 1->0
@pytest.mark.valid_from("Frontier")
def test_xen_approve_delete_existing_slots(
    blockchain_test: BlockchainTestFiller, pre: Alloc
) -> None:
    """
    Uses the `approve(address,uint256)` method of XEN (ERC20) close to the maximum amount
    of slots which could be edited (as opposed to be created) within a single block/transaction.
    """
    attack_gas_limit = (
        60_000_000  # TODO: currently hardcoded, should be read from `gas_benchmark_value`
    )

    # 22 Sep 10:08:22 | Processed            23366464         |      207.4 ms  | slot          1,734 ms |⛽ Gas gwei: 1.00 .. 1.00 (1.00) .. 1.00
    # 22 Sep 10:08:22 | Cleared caches: Rlp
    # 22 Sep 10:08:22 |  Block    0.0600 ETH    59.96 MGas    |        1   txs | calls      7,752 (  0) | sload       8 | sstore  7,762 | create   0
    # 22 Sep 10:08:22 |  Block throughput      289.05 MGas/s  |        4.8 tps |             4.82 Blk/s | exec code cache  15,508 | new      0 | ops   1,868,419

    # Gas limit: 60M, 2424 SSTOREs, 300 MGas/s

    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8
    usdt_contract = 0xDAC17F958D2EE523A2206206994597C13D831EC7  # Used in intermediate blocks to attempt to bust te cache
    gas_threshold = 40_000

    fn_signature_approve = bytes.fromhex(
        "095EA7B3"
    )  # Function selector of `approve(address,uint256)`
    # This code loops until there is less than threshold_gas left and reads two items from calldata:
    # The first 32 bytes are interpreted as the start address to start approving for
    # The second 32 bytes is the approval amount
    # This can thus be used to initialize the approvals (in multiple txs) to write to the storage
    # Since initializing storage (from zero to nonzero) is more expensive, this thus has
    # to be done over multiple blocks/txs
    # The attack block can then target all of the just initialized storage slots to edit
    # (This should thus yield more dirty trie nodes than the )
    approval_loop_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, Op.CALLDATALOAD(32))
        + Op.CALLDATALOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=xen_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            # + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 34), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
    )

    approval_spammer_contract = pre.deploy_contract(code=approval_loop_code)

    usdt_approve_spammer_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, 1)
        + Op.SLOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=usdt_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            # + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 34), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.PUSH1(0)
        + Op.SSTORE
    )
    # Set storage to value 1 to avoid paying 20k on the update
    usdt_approve_spammer_contract = pre.deploy_contract(
        code=usdt_approve_spammer_code, storage={0: 1}
    )

    sender = pre.fund_eoa()
    sender2 = pre.fund_eoa()  # More senders to get more chance to get a semi-full block
    sender3 = (
        pre.fund_eoa()
    )  # If done from one sender, Nethermind's block builder only includes 1 tx
    sender4 = pre.fund_eoa()
    sender5 = pre.fund_eoa()

    blocks = []

    # TODO: calculate these constants based on the gas limit of the benchmark test
    start_address = 0x01  # Start at address 1, address 0 cannot be approved
    current_address = start_address
    address_incr = 2000

    approval_value_fresh = Hash(0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFE)
    approval_value_overwrite = Hash(0)

    block_count = 10

    for _ in range(block_count):
        setup_calldata = Hash(current_address) + approval_value_fresh
        setup_tx = Transaction(
            to=approval_spammer_contract,
            gas_limit=attack_gas_limit,
            data=setup_calldata,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[setup_tx]))

        current_address += address_incr

    spam_count = 200

    for _ in range(spam_count):
        # NOTE: USDC does not allow changing the approval value. It first has to be
        # set to zero before it changes. We therefore flood USDC with approvals in an
        # attempt to bust the cache
        spam_tx = Transaction(
            to=usdt_approve_spammer_contract,
            gas_limit=attack_gas_limit // 2,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[spam_tx]))

    attack_calldata = Hash(start_address) + approval_value_overwrite

    attack_tx = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit,
        max_priority_fee_per_gas=100,
        max_fee_per_gas=10000,
        data=attack_calldata,
        sender=sender,
    )
    # Take into account the max refunds (which will be awarded here)
    # The previous tx will also not completely use all gas since it jumps out of the loop early
    # to avoid that the whole tx OOGs
    # TODO: make this attack gas limit dependent
    # It should be sufficient to assume full refund and to send the whole block as gas limit initially
    # The next tx gas limit is thus (if refund is maximally applied) 20% of the original
    # Repeat this until the intrinsic costs cannot be paid
    attack_tx_2 = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit // 5,
        max_priority_fee_per_gas=90,
        max_fee_per_gas=9000,
        data=Hash(8000) + approval_value_overwrite,
        sender=sender2,
    )
    attack_tx_3 = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit // (5 * 5),
        max_priority_fee_per_gas=80,
        max_fee_per_gas=8000,
        data=Hash(12000) + approval_value_overwrite,
        sender=sender3,
    )
    attack_tx_4 = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit // (5 * 5 * 5),
        max_priority_fee_per_gas=80,
        max_fee_per_gas=8000,
        data=Hash(16000) + approval_value_overwrite,
        sender=sender4,
    )
    attack_tx_5 = Transaction(
        to=approval_spammer_contract,
        gas_limit=attack_gas_limit // (5 * 5 * 5 * 5),
        max_priority_fee_per_gas=80,
        max_fee_per_gas=8000,
        data=Hash(18000) + approval_value_overwrite,
        sender=sender5,
    )

    blocks.append(
        Block(txs=[attack_tx, attack_tx_2, attack_tx_3, attack_tx_4, attack_tx_5])
    )  # , #attack_tx_2, attack_tx_3]))

    blockchain_test(
        pre=pre,
        post={},  # TODO: add sanity checks (succesful tx execution and no out-of-gas)
        blocks=blocks,
        skip_gas_used_validation=True,
    )


# TODO
# The current test does only claimRank(1) and then waits `SECONDS_IN_DAY = 3_600 * 24;` plus 1
# (see https://etherscan.io/token/0x06450dEe7FD2Fb8E39061434BAbCFC05599a6Fb8#code) and then
# claimMintReward() from CREATE2-create proxy accounts (to save gas).
# This might not be the worst scenario, for instance `claimMintRewardAndShare(address,uint256)`
# might yield even worse scenarios (or scenarios regarding "staking")
# These scenarios will be added.


# TODO: set correct fork, XEN might reject on historical forks due to e.g. non-existent opcodes
# NOTE: deploy both XEN (0x06450dEe7FD2Fb8E39061434BAbCFC05599a6Fb8)
# and Math (0x4bBA9B6B49f3dFA6615f079E9d66B0AA68B04A4d) in prestate for the Mainnet scenario!
# NOTE: this requires the timestamp hack, where each new payload moves by at least 24*60*60+1
# seconds (fix me later if we have the tooling for this)
@pytest.mark.valid_from("Frontier")
def test_xen_claimrank_and_mint(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    pre: Alloc,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """Simple XEN scenario to claimRank(1) and claimMintReward()."""
    # NOTE: the XEN tests are currently hardcoded against a gas limit.
    # To expand this to read from `gas_benchmark_value`, we need to calculate the necessary
    # amount of `num_xen` based on that gas limit (which is a complex formula as this is based
    # on the gas used by the XEN contract)
    attack_gas_limit = 60_000_000  # TODO: also run me for 100M.
    # fee_recipient = pre.fund_eoa(amount=1)

    # timestamp to use for the initial block. Timestamp of later blocks are manually added/changed.
    # timestamp = 12 TODO: disabled, this is likely not part of EEST to support
    # A special CL has to perform edited newPayloads such that we can edit the timestamp

    # NOTE: these contracts MUST be specified for this test to work
    # TODO: check how/if EEST enforces this
    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8
    # NOTE: from the test perspective this contract should not be specified
    # However, the XEN contract needs the Math contract. If this is not provided, the transaction
    # will likely revert ("fail"). This is not what we want. We want state bloat!
    #    pre.deploy_contract("", label="MATH_CONTRACT")

    # This is after (!!) deployment (so step 2, not 1): claimMintReward()
    calldata_claim_mint_reward = bytes.fromhex("52c7f8dc")
    # Calldata for claimRank(1)
    calldata_claim_rank = bytes.fromhex(
        "9ff054df0000000000000000000000000000000000000000000000000000000000000001"
    )
    after_initcode_callata = (
        Om.MSTORE(bytes.fromhex("52c7f8dc"), offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_mint_reward),
        )
        + Om.MSTORE(calldata_claim_rank, offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_rank),
        )
    )

    # claimRank(1) and deposits the code to claimMintReward() if this contract is called
    # + claimRank(1) again
    initcode = (
        Om.MSTORE(calldata_claim_rank, offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_rank),
        )
        + Om.MSTORE(after_initcode_callata, offset=0)
        + Op.RETURN(0, len(after_initcode_callata))
    )

    # Template code that will be used to deploy a large number of contracts.
    initcode_address = pre.deploy_contract(code=initcode)

    # `claimMintReward()` as the performance test.

    factory_code = (
        Op.EXTCODECOPY(
            address=initcode_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(initcode_address),
        )
        + Op.MSTORE(
            0,
            Op.CREATE2(
                offset=0,
                size=Op.EXTCODESIZE(initcode_address),
                salt=Op.SLOAD(0),
            ),
        )
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.RETURN(0, 32)
    )

    factory_address = pre.deploy_contract(code=factory_code)

    factory_gas_threshold = 400_000

    factory_caller_code = While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.GT(Op.GAS, factory_gas_threshold),
    )
    factory_caller_address = pre.deploy_contract(code=factory_caller_code)

    sender = pre.fund_eoa()

    gas_threshold = 400_000

    code = (
        # Setup memory for later CREATE2 address generation loop.
        # 0xFF+[Address(20bytes)]+[seed(32bytes)]+[initcode keccak(32bytes)]
        Op.MSTORE(0, factory_address)
        + Op.MSTORE8(32 - 20 - 1, 0xFF)
        + Op.MSTORE(32, 0)  # NOTE: this memory location is used as start index of the contracts.
        + Op.MSTORE(64, initcode.keccak256())
        # Main loop
        + While(
            body=Op.POP(Op.CALL(address=Op.SHA3(32 - 20 - 1, 85)))
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
            # Loop over `CALLDATALOAD` contracts
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    assert len(code) <= fork.max_code_size()

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, storage={0: 1})

    post = {
        code_addr: Account(storage={0: 42}),  # Check for successful execution.
    }
    # deployed_contract_addresses = []
    # for i in range(num_contracts):
    #    deployed_contract_address = compute_create2_address(
    #        address=factory_address,
    #        salt=i,
    ##        initcode=initcode,
    #   )
    #    post[deployed_contract_address] = Account(nonce=1)
    #    deployed_contract_addresses.append(deployed_contract_address)

    blocks = []
    for _ in range(10):  # Check how much of these we need
        contracts_deployment_tx = Transaction(
            to=factory_caller_address,
            gas_limit=attack_gas_limit,
            sender=sender,
        )
        blocks.append(Block(txs=[contracts_deployment_tx]))

    fn_signature_approve = bytes.fromhex("095EA7B3")
    usdt_contract = 0xDAC17F958D2EE523A2206206994597C13D831EC7  # Used in intermediate blocks to attempt to bust te cache
    usdt_approve_spammer_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, 1)
        + Op.SLOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=usdt_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            # + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 34), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.PUSH1(0)
        + Op.SSTORE
    )
    # Set storage to value 1 to avoid paying 20k on the update
    usdt_approve_spammer_contract = pre.deploy_contract(
        code=usdt_approve_spammer_code, storage={0: 1}
    )

    spam_count = 200

    for _ in range(spam_count):
        # NOTE: USDC does not allow changing the approval value. It first has to be
        # set to zero before it changes. We therefore flood USDC with approvals in an
        # attempt to bust the cache
        spam_tx = Transaction(
            to=usdt_approve_spammer_contract,
            gas_limit=attack_gas_limit // 2,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[spam_tx]))

    # for _ in range(24*60*60):
    #    blocks.append(Block(txs=[Transaction(sender=sender,to=sender, nonce=sender_nonce)]))
    #    sender_nonce = sender_nonce + 1

    opcode_tx = Transaction(
        to=code_addr,
        gas_limit=attack_gas_limit,
        sender=sender,
    )

    attack_block = Block(
        txs=[opcode_tx],
        # NOTE: timestamp has no effect in `uv execute remote`. Forcing test to produce 24*60*60 blocks.
        # It is guaranteed that the timestamp increases each block, so each block will at least move time
        # by a second.
        # Set timestamp such that XEN bond matures
        # See `MIN_TERM` constant in XEN source
        # timestamp=timestamp + 3_600 * 24,
    )
    blocks.append(attack_block)

    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        exclude_full_post_state_in_output=True,
        skip_gas_used_validation=True,
    )


@pytest.mark.valid_from("Frontier")
def test_xen_claimrank_and_share_mint(
    blockchain_test: BlockchainTestFiller,
    fork: Fork,
    pre: Alloc,
    env: Environment,
    gas_benchmark_value: int,
) -> None:
    """XEN scenario mimicking mainnet slow blocks, e.g. tx 0xc155aff9732f6ad9409339d28ba841b14dd181884450b3c0274672b17f2fa59a"""
    # NOTE: the XEN tests are currently hardcoded against a gas limit.
    # To expand this to read from `gas_benchmark_value`, we need to calculate the necessary
    # amount of `num_xen` based on that gas limit (which is a complex formula as this is based
    # on the gas used by the XEN contract)
    attack_gas_limit = 60_000_000  # TODO: also run me for 100M.
    # fee_recipient = pre.fund_eoa(amount=1)

    # timestamp to use for the initial block. Timestamp of later blocks are manually added/changed.
    # timestamp = 12 TODO: disabled, this is likely not part of EEST to support
    # A special CL has to perform edited newPayloads such that we can edit the timestamp

    # NOTE: these contracts MUST be specified for this test to work
    # TODO: check how/if EEST enforces this
    xen_contract = 0x06450DEE7FD2FB8E39061434BABCFC05599A6FB8
    # NOTE: from the test perspective this contract should not be specified
    # However, the XEN contract needs the Math contract. If this is not provided, the transaction
    # will likely revert ("fail"). This is not what we want. We want state bloat!
    #    pre.deploy_contract("", label="MATH_CONTRACT")

    # This is after (!!) deployment (so step 2, not 1): claimMintRewardAndShare(x, 100)
    # TODO: use another target address
    # NOTE: this sends 100% of the minted tokens to this address. Play around with sending half of the tokens
    # then the other half gets awarded to self.
    # Most likely: this specific input (100% to one account) will trigger SSTORE(x, 0) on a non-existing slot
    # This in particular, especially because it happens a lot in this block, might cause these slow blocks

    calldata_claim_mint_reward_and_share = bytes.fromhex(
        "1c56030500000000000000000000000006b1767503aec0d3e827cd27bb016f00f1cec8620000000000000000000000000000000000000000000000000000000000000064"
    )
    # Calldata for claimRank(1)
    calldata_claim_rank = bytes.fromhex(
        "9ff054df0000000000000000000000000000000000000000000000000000000000000001"
    )
    after_initcode_callata = (
        Om.MSTORE(calldata_claim_mint_reward_and_share, offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_mint_reward_and_share),
        )
        + Om.MSTORE(calldata_claim_rank, offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_rank),
        )
    )

    # claimRank(1) and deposits the code to claimMintReward() if this contract is called
    # + claimRank(1) again
    initcode = (
        Om.MSTORE(calldata_claim_rank, offset=0)
        + Op.CALL(
            address=(xen_contract),
            args_size=len(calldata_claim_rank),
        )
        + Om.MSTORE(after_initcode_callata, offset=0)
        + Op.RETURN(0, len(after_initcode_callata))
    )

    # Template code that will be used to deploy a large number of contracts.
    initcode_address = pre.deploy_contract(code=initcode)

    # `claimMintReward()` as the performance test.

    factory_code = (
        Op.EXTCODECOPY(
            address=initcode_address,
            dest_offset=0,
            offset=0,
            size=Op.EXTCODESIZE(initcode_address),
        )
        + Op.MSTORE(
            0,
            Op.CREATE2(
                offset=0,
                size=Op.EXTCODESIZE(initcode_address),
                salt=Op.SLOAD(0),
            ),
        )
        + Op.SSTORE(0, Op.ADD(Op.SLOAD(0), 1))
        + Op.RETURN(0, 32)
    )

    factory_address = pre.deploy_contract(code=factory_code)

    factory_gas_threshold = 400_000

    factory_caller_code = While(
        body=Op.POP(Op.CALL(address=factory_address)),
        condition=Op.GT(Op.GAS, factory_gas_threshold),
    )
    factory_caller_address = pre.deploy_contract(code=factory_caller_code)

    sender = pre.fund_eoa()

    gas_threshold = 400_000

    code = (
        # Setup memory for later CREATE2 address generation loop.
        # 0xFF+[Address(20bytes)]+[seed(32bytes)]+[initcode keccak(32bytes)]
        Op.MSTORE(0, factory_address)
        + Op.MSTORE8(32 - 20 - 1, 0xFF)
        + Op.MSTORE(32, 0)  # NOTE: this memory location is used as start index of the contracts.
        + Op.MSTORE(64, initcode.keccak256())
        # Main loop
        + While(
            body=Op.POP(Op.CALL(address=Op.SHA3(32 - 20 - 1, 85)))
            + Op.MSTORE(32, Op.ADD(Op.MLOAD(32), 1)),
            # Loop over `CALLDATALOAD` contracts
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.SSTORE(0, 42)  # Done for successful tx execution assertion below.
    )
    assert len(code) <= fork.max_code_size()

    # The 0 storage slot is initialize to avoid creation costs in SSTORE above.
    code_addr = pre.deploy_contract(code=code, storage={0: 1})

    post = {
        code_addr: Account(storage={0: 42}),  # Check for successful execution.
    }
    # deployed_contract_addresses = []
    # for i in range(num_contracts):
    #    deployed_contract_address = compute_create2_address(
    #        address=factory_address,
    #        salt=i,
    ##        initcode=initcode,
    #   )
    #    post[deployed_contract_address] = Account(nonce=1)
    #    deployed_contract_addresses.append(deployed_contract_address)

    blocks = []
    for _ in range(10):  # Check how much of these we need
        contracts_deployment_tx = Transaction(
            to=factory_caller_address,
            gas_limit=attack_gas_limit,
            sender=sender,
        )
        blocks.append(Block(txs=[contracts_deployment_tx]))

    fn_signature_approve = bytes.fromhex("095EA7B3")
    usdt_contract = 0xDAC17F958D2EE523A2206206994597C13D831EC7  # Used in intermediate blocks to attempt to bust te cache
    usdt_approve_spammer_code = (
        Om.MSTORE(fn_signature_approve)
        + Op.MSTORE(4 + 32, 1)
        + Op.SLOAD(0)
        + While(
            body=Op.MSTORE(
                4, Op.DUP1
            )  # Put a copy of the topmost stack item in memory (this is the target address)
            + Op.CALL(address=usdt_contract, args_offset=0, args_size=4 + 32 + 32)
            + Op.ADD,  # Add the status of the CALL
            # (this should always be 1 unless the `gas_threshold` is too low) to the stack item
            # The address and thus target storage slot changes!
            # + Op.MSTORE(4 + 32, Op.SUB(Op.MLOAD(4 + 34), Op.GAS)),
            condition=Op.GT(Op.GAS, gas_threshold),
        )
        + Op.PUSH1(0)
        + Op.SSTORE
    )
    # Set storage to value 1 to avoid paying 20k on the update
    usdt_approve_spammer_contract = pre.deploy_contract(
        code=usdt_approve_spammer_code, storage={0: 1}
    )

    spam_count = 200

    for _ in range(spam_count):
        # NOTE: USDC does not allow changing the approval value. It first has to be
        # set to zero before it changes. We therefore flood USDC with approvals in an
        # attempt to bust the cache
        spam_tx = Transaction(
            to=usdt_approve_spammer_contract,
            gas_limit=attack_gas_limit // 2,
            sender=sender,
            max_priority_fee_per_gas=100,
            max_fee_per_gas=10000,
        )
        blocks.append(Block(txs=[spam_tx]))

    # for _ in range(24*60*60):
    #    blocks.append(Block(txs=[Transaction(sender=sender,to=sender, nonce=sender_nonce)]))
    #    sender_nonce = sender_nonce + 1

    opcode_tx = Transaction(
        to=code_addr,
        gas_limit=attack_gas_limit,
        sender=sender,
    )

    attack_block = Block(
        txs=[opcode_tx],
        # NOTE: timestamp has no effect in `uv execute remote`. Forcing test to produce 24*60*60 blocks.
        # It is guaranteed that the timestamp increases each block, so each block will at least move time
        # by a second.
        # Set timestamp such that XEN bond matures
        # See `MIN_TERM` constant in XEN source
        # timestamp=timestamp + 3_600 * 24,
    )
    blocks.append(attack_block)

    blockchain_test(
        pre=pre,
        post=post,
        blocks=blocks,
        exclude_full_post_state_in_output=True,
        skip_gas_used_validation=True,
    )
