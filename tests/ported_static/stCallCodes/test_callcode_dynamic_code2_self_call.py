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
from execution_testing.forks import Fork
from execution_testing.specs.static_state.expect_section import (
    resolve_expect_post,
)
from execution_testing.vm import Op

REFERENCE_SPEC_GIT_PATH = "N/A"
REFERENCE_SPEC_VERSION = "N/A"

TX_DATA = [
    "000000000000000000000000a000000000000000000000000000000000000000",
    "0000000000000000000000001000000000000000000000000000000000000000",
]

TX_GAS = [1453081]

TX_VALUE = [0]


def _tx_data(d: int) -> bytes:
    """Convert TX_DATA[d] hex string to bytes."""
    return bytes.fromhex(TX_DATA[d]) if TX_DATA[d] else b""


@pytest.mark.ported_from(
    [
        "tests/static/state_tests/stCallCodes/callcodeDynamicCode2SelfCallFiller.json",  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(0, 0, 0, id="case0"),
        pytest.param(1, 0, 0, id="case1"),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_callcode_dynamic_code2_self_call(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
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
    callee = pre.deploy_contract(
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
    callee_1 = pre.deploy_contract(
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

    expect_entries_: list[dict] = [
        {
            "indexes": {"data": 0, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    code=bytes.fromhex(
                        "604680602760003960006000f0600a5560406000604060006000600a54620186a0f2600b5500fe604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e620186a0f2607a5560128060346000396000f300fe600160005530601455326015553360165500"  # noqa: E501
                    )
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600035620c3500f100"
                    )
                ),
                Address("0x7db299e0885c85039f56fa504a13dd8ce8a56aa7"): Account(
                    storage={
                        11: 1,
                        12: 0xA000000000000000000000000000000000000000,
                    }
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e626000527f0186a0f2600b5533600c55000000000000000000000000000000000000000000602052604060006001f000"  # noqa: E501
                    )
                ),
            },
        },
        {
            "indexes": {"data": 1, "gas": 0, "value": 0},
            "network": [">=Cancun"],
            "result": {
                callee: Account(
                    storage={
                        0: 1,
                        10: 0x13136008B64FF592819B2FA6D43F2835C452020E,
                        11: 1,
                        20: 0x1000000000000000000000000000000000000000,
                        21: 0xA94F5374FCE5EDBC8E2A8697C15331677E6EBF0B,
                        22: 0x1000000000000000000000000000000000000000,
                    },
                    code=bytes.fromhex(
                        "604680602760003960006000f0600a5560406000604060006000600a54620186a0f2600b5500fe604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e620186a0f2607a5560128060346000396000f300fe600160005530601455326015553360165500"  # noqa: E501
                    ),
                ),
                contract: Account(
                    code=bytes.fromhex(
                        "60006000600060006000600035620c3500f100"
                    )
                ),
                Address("0x13136008b64ff592819b2fa6d43f2835c452020e"): Account(
                    storage={122: 1},
                    code=bytes.fromhex("600160005530601455326015553360165500"),
                ),
                callee_1: Account(
                    code=bytes.fromhex(
                        "7f604060006040600060007313136008b64ff592819b2fa6d43f2835c452020e626000527f0186a0f2600b5533600c55000000000000000000000000000000000000000000602052604060006001f000"  # noqa: E501
                    )
                ),
            },
        },
    ]

    post, _exc = resolve_expect_post(expect_entries_, d, g, v, fork)

    tx = Transaction(
        sender=sender,
        to=contract,
        data=_tx_data(d),
        gas_limit=TX_GAS[g],
        value=TX_VALUE[v],
        error=_exc,
    )

    state_test(env=env, pre=pre, post=post, tx=tx)
