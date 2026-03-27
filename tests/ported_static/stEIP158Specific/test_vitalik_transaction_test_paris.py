"""
Test_vitalik_transaction_test_paris.

Ported from:
state_tests/stEIP158Specific/vitalikTransactionTestParisFiller.json
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

REFERENCE_SPEC_GIT_PATH = "N/A"

REFERENCE_SPEC_VERSION = "N/A"


@pytest.mark.ported_from(
    ["state_tests/stEIP158Specific/vitalikTransactionTestParisFiller.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_vitalik_transaction_test_paris(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_vitalik_transaction_test_paris."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    contract_0 = Address("0xee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4")
    sender = EOA(
        key=0xC85EF7D79691FE79573B1A7064C19C1A9819EBDBD1FAAAB1A8EC92344438AAF4
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        difficulty=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    pre[coinbase] = Account(balance=0, nonce=1)
    pre[sender] = Account(balance=0xFFFFFFFFFFFFFFFFFFFF, nonce=335)
    # Source: hex
    # 0x
    contract_0 = pre.deploy_contract(  # noqa: F841
        code="",
        balance=10,
        nonce=0,
        address=Address("0xee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4"),  # noqa: E501
    )

    tx = Transaction(
        sender=sender,
        to=None,
        data=bytes.fromhex(
            "6000607f5359610043806100135939610056566c010000000000000000000000007fee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4d53532071d6cd0cb86facd5605ff6100008061003f60003961003f565b6000f35b816000f0905050596100718061006c59396100dd5661005f8061000e60003961006d566000603f5359610043806100135939610056566c010000000000000000000000007fee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4d53532071d6cd0cb86facd5605ff6100008061003f60003961003f565b6000f35b816000f0905050fe5b6000f35b816000f0905060405260006000600060006000604051620249f0f15061000080610108600039610108565b6000f3"  # noqa: E501
        ),
        gas_limit=2097151,
        nonce=335,
        gas_price=10,
    )

    post = {
        coinbase: Account(storage={}, code=b"", nonce=1),
        sender: Account(storage={}, code=b"", nonce=336),
        Address("0x1bc78ae0e5ec5cb439f1d5355d6f90d38343e109"): Account(
            storage={}, code=b"", nonce=3
        ),
        Address("0x51f9d7f98e997bdd6bebde4c2dd27be8c99303aa"): Account(
            storage={},
            code=bytes.fromhex(
                "6000603f5359610043806100135939610056566c010000000000000000000000007fee098e6c2a43d9e2c04f08f0c3a87b0ba59079d4d53532071d6cd0cb86facd5605ff6100008061003f60003961003f565b6000f35b816000f0905050fe"  # noqa: E501
            ),
            balance=0,
            nonce=1,
        ),
        contract_0: Account(storage={}, code=b"", balance=10, nonce=0),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
