"""
callcode happen to a contract that is dynamically created from within the...

Ported from:
tests/static/state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json
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
        "tests/static/state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "tx_data_hex, expected_post",
    [
        (
            "000000000000000000000000a000000000000000000000000000000000000000",
            {
                Address("0x7db299e0885c85039f56fa504a13dd8ce8a56aa7"): Account(
                    storage={
                        11: 1,
                        12: 0xA000000000000000000000000000000000000000,
                    }
                )
            },
        ),
        (
            "0000000000000000000000001000000000000000000000000000000000000000",
            {
                Address("0x1000000000000000000000000000000000000000"): Account(
                    storage={
                        0: 1,
                        10: 0x13136008B64FF592819B2FA6D43F2835C452020E,
                        11: 1,
                        20: 0x1000000000000000000000000000000000000000,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0x1000000000000000000000000000000000000000,
                    }
                ),
                Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                    storage={122: 1}
                ),
            },
        ),
    ],
    ids=["case0", "case1"],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
    tx_data_hex: str,
    expected_post: dict,
) -> None:
    """Callcode happen to a contract that is dynamically created from..."""
    coinbase = Address("0x2adc25665018aa1fe0e6bc666dac8fc2697ff9ba")
    sender = EOA(
        key=0x45A915E4D060149EB4365960E6A7A45F334393093061116B197E3240065FF2D8
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=10000000,
    )

    # Source: LLL
    # {(seq [[10]] (CREATE 0 0 (lll(seq  [[122]] (CALLCODE 100000 0x13136008b64ff592819b2fa6d43f2835c452020e 0 0 64 0 64)  (RETURN 0 (lll(seq [[0]] 1  [[20]] (ADDRESS) [[21]] (ORIGIN) [[22]] (CALLER)   )0) )  )0)   )  [[11]] (CALLCODE 100000 (SLOAD 10) 0 0 64 0 64)                   )}  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.PUSH1[0x46]
            + Op.CODECOPY(dest_offset=0x0, offset=0x27, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.PUSH1[0x0]
            + Op.SSTORE(key=0xA, value=Op.CREATE)
            + Op.SSTORE(
                key=0xB,
                value=Op.CALLCODE(
                    gas=0x186A0,
                    address=Op.SLOAD(key=0xA),
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(
                key=0x7A,
                value=Op.CALLCODE(
                    gas=0x186A0,
                    address=0x13136008B64FF592819B2FA6D43F2835C452020E,
                    value=0x0,
                    args_offset=0x0,
                    args_size=0x40,
                    ret_offset=0x0,
                    ret_size=0x40,
                ),
            )
            + Op.PUSH1[0x12]
            + Op.CODECOPY(dest_offset=0x0, offset=0x34, size=Op.DUP1)
            + Op.PUSH1[0x0]
            + Op.RETURN
            + Op.STOP
            + Op.INVALID
            + Op.SSTORE(key=0x0, value=0x1)
            + Op.SSTORE(key=0x14, value=Op.ADDRESS)
            + Op.SSTORE(key=0x15, value=Op.ORIGIN)
            + Op.SSTORE(key=0x16, value=Op.CALLER)
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0x1000000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # { (CALL 800000 (CALLDATALOAD 0) 0 0 0 0 0) }
    contract = pre.deploy_contract(
        code=(
            Op.CALL(
                gas=0xC3500,
                address=Op.CALLDATALOAD(offset=0x0),
                value=0x0,
                args_offset=0x0,
                args_size=0x0,
                ret_offset=0x0,
                ret_size=0x0,
            )
            + Op.STOP
        ),
        nonce=0,
        address=Address("0x1100000000000000000000000000000000000000"),  # noqa: E501
    )
    # Source: LLL
    # {  (MSTORE 0 0x604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e62) (MSTORE 32 0x0186a0f2600b5533600c55000000000000000000000000000000000000000000)  (CREATE 1 0 64) }  # noqa: E501
    pre.deploy_contract(
        code=(
            Op.MSTORE(
                offset=0x0,
                value=0x604060006040600060007313136008B64FF592819B2FA6D43F2835C452020E62,  # noqa: E501
            )
            + Op.MSTORE(
                offset=0x20,
                value=0x186A0F2600B5533600C55000000000000000000000000000000000000000000,  # noqa: E501
            )
            + Op.CREATE(value=0x1, offset=0x0, size=0x40)
            + Op.STOP
        ),
        balance=0x2710,
        nonce=0,
        address=Address("0xa000000000000000000000000000000000000000"),  # noqa: E501
    )
    pre[sender] = Account(balance=0x2386F26FC10000)

    tx_data = bytes.fromhex(tx_data_hex) if tx_data_hex else b""

    tx = Transaction(
        sender=sender,
        to=contract,
        data=tx_data,
        gas_limit=1453081,
    )

    post = expected_post

    state_test(env=env, pre=pre, post=post, tx=tx)
