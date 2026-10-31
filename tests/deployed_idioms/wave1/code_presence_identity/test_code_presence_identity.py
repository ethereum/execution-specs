"""
Archetype 22: code presence as an identity test.

`isContract(a) == (a.code.length > 0)` is one of the most widely deployed
idioms on mainnet. L2 measured the `EXTCODESIZE`-gate shape at **618,693
distinct runtime code hashes across 2,417,615 addresses**, FP 0/8 — the
second-largest population in the corpus.

**This class exists because a fork can change semantics without changing any
price.** The rest of this catalogue is gas-shaped; nothing in it can express
this invariant, and no repricing breaks it. EIP-7702 breaks it outright, and
already shipped.

A delegated EOA stores `EOA_DELEGATION_MARKER || address`, where the marker is
`b"\\xef\\x01\\x00"` (`vm/eoa_delegation.py:36`), giving **23 bytes** of code.
`EXTCODESIZE` pushes `U256(len(code))` with no delegation resolution
(`vm/instructions/environment.py:357`). So from Prague onward:

```
isContract(a delegated EOA) == true
```

Every deployed `require(!isContract(x))`, every "reject contracts" gate, and
every "this must be a wallet" check silently changes meaning for any EOA that
has ever signed an authorization. The account is still an EOA: it can send
transactions and hold a nonce.

The invariant asserted is therefore the *correct* one, split by fork: code
presence identifies a contract before Prague, and does not after.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    AuthorizationTuple,
    Op,
    StateTestFiller,
    Storage,
    Transaction,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

# b"\xef\x01\x00" (3) + a 20-byte address. A semantic constant, not a cost.
DELEGATION_DESIGNATOR_LENGTH = 23


@pytest.mark.valid_from("Berlin")
def test_code_presence_identifies_a_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test `EXTCODESIZE > 0` separates a plain EOA from a contract.

    The sound form of the invariant, asserted on every fork: an account with
    no code is not a contract, and an account with code is. Both arms are in
    one test so the discriminator is pinned rather than assumed.
    """
    eoa = pre.fund_eoa()
    contract = pre.deploy_contract(Op.STOP)

    eoa_storage = Storage()
    eoa_probe = pre.deploy_contract(
        Op.SSTORE(eoa_storage.store_next(0, "eoa_is_contract"),
                  Op.GT(Op.EXTCODESIZE(eoa), 0))
        + Op.SSTORE(eoa_storage.store_next(0, "eoa_code_size"),
                    Op.EXTCODESIZE(eoa))
        + Op.STOP
    )
    contract_storage = Storage()
    contract_probe = pre.deploy_contract(
        Op.SSTORE(contract_storage.store_next(1, "contract_is_contract"),
                  Op.GT(Op.EXTCODESIZE(contract), 0))
        + Op.STOP
    )

    entry = pre.deploy_contract(
        Op.POP(Op.CALL(gas=Op.GAS, address=eoa_probe))
        # Forward GAS, not a literal: a literal 100,000 is below the measured
        # Amsterdam floor of ~110,026 for creating one storage slot, so this
        # test's own control would out-of-gas there. That is archetype 1
        # applying to this corpus's own test code.
        + Op.POP(Op.CALL(gas=Op.GAS, address=contract_probe))
        + Op.STOP
    )
    tx = Transaction(to=entry, state_gas_reservoir=0, sender=pre.fund_eoa())
    state_test(
        pre=pre,
        post={
            eoa_probe: Account(storage=eoa_storage),
            contract_probe: Account(storage=contract_storage),
        },
        tx=tx,
    )


@pytest.mark.valid_from("Prague")
def test_code_presence_no_longer_identifies_a_contract(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """
    Test a delegated EOA reports code, so `isContract` answers wrongly.

    The signer is an externally owned account throughout -- it signed an
    authorization, nothing more. Yet it carries a 23-byte delegation
    designator, so every deployed `EXTCODESIZE`-based gate now classifies it
    as a contract. Both the boolean and the exact designator length are
    asserted: the boolean is the harm, and the length pins the designator
    format that produces it.
    """
    impl = pre.deploy_contract(Op.STOP)
    signer = pre.fund_eoa()

    storage = Storage()
    probe = pre.deploy_contract(
        Op.SSTORE(storage.store_next(1, "delegated_eoa_reads_as_contract"),
                  Op.GT(Op.EXTCODESIZE(signer), 0))
        + Op.SSTORE(storage.store_next(DELEGATION_DESIGNATOR_LENGTH,
                                       "designator_length"),
                    Op.EXTCODESIZE(signer))
        + Op.STOP
    )

    tx = Transaction(
        to=probe,
        state_gas_reservoir=0,
        sender=pre.fund_eoa(),
        authorization_list=[
            AuthorizationTuple(address=impl, nonce=0, signer=signer)
        ],
    )
    state_test(pre=pre, post={probe: Account(storage=storage)}, tx=tx)
