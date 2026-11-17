"""
Call the daily limit functions of the `daylimit` contract.

Ported from:
state_tests/stWalletTest/dayLimitResetSpentTodayFiller.json
state_tests/stWalletTest/dayLimitSetDailyLimitFiller.json
state_tests/stWalletTest/dayLimitSetDailyLimitNoDataFiller.json

@manually-enhanced: Do not overwrite. Merged; derived storage slots.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Hash,
    StateTestFiller,
    Transaction,
)

from tests.ported_static.stWalletTest.wallet_contracts import (
    DAILY_LIMIT_SLOT,
    DAY_LIMIT_CODE,
    LAST_DAY_SLOT,
    PENDING_INDEX_SLOT,
    SPENT_TODAY_SLOT,
    owners_storage,
)

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

RESET_SPENT_TODAY = Bytes("5c52c2f5")
SET_DAILY_LIMIT = Bytes("b20d30a9")
LAST_DAY = 0xC22E4


@pytest.mark.ported_from(
    [
        "state_tests/stWalletTest/dayLimitResetSpentTodayFiller.json",
        "state_tests/stWalletTest/dayLimitSetDailyLimitFiller.json",
        "state_tests/stWalletTest/dayLimitSetDailyLimitNoDataFiller.json",
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "scenario",
    ["reset_spent_today", "set_daily_limit", "set_daily_limit_no_data"],
)
def test_day_limit(
    state_test: StateTestFiller,
    pre: Alloc,
    scenario: str,
) -> None:
    """Call one `daylimit` function from the single owner."""
    sender = pre.fund_eoa()
    storage = owners_storage(1, [sender]) | {LAST_DAY_SLOT: LAST_DAY}

    data: bytes
    if scenario == "reset_spent_today":
        storage |= {
            PENDING_INDEX_SLOT: 1,
            DAILY_LIMIT_SLOT: 2,
            SPENT_TODAY_SLOT: 5,
        }
        data = RESET_SPENT_TODAY
        post_storage = storage | {PENDING_INDEX_SLOT: 2, SPENT_TODAY_SLOT: 0}
    elif scenario == "set_daily_limit":
        data = SET_DAILY_LIMIT + Hash(2)
        post_storage = storage | {PENDING_INDEX_SLOT: 1, DAILY_LIMIT_SLOT: 2}
    elif scenario == "set_daily_limit_no_data":
        data = SET_DAILY_LIMIT
        post_storage = storage | {PENDING_INDEX_SLOT: 1}
    else:
        raise ValueError(f"Unknown scenario: {scenario}")

    wallet = pre.deploy_contract(code=DAY_LIMIT_CODE, storage=storage)
    tx = Transaction(sender=sender, to=wallet, data=data)
    state_test(pre=pre, post={wallet: Account(storage=post_storage)}, tx=tx)
