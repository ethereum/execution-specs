"""
Test_random_statetest642.

Ported from:
state_tests/stRandom2/randomStatetest642Filler.json
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
    ["state_tests/stRandom2/randomStatetest642Filler.json"],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.pre_alloc_mutable
def test_random_statetest642(
    state_test: StateTestFiller,
    pre: Alloc,
) -> None:
    """Test_random_statetest642."""
    addr_2 = Address(0x78D51368C50ED27350D847254125276522CF9DAC)
    sender = EOA(
        key=0x776D5E84B9AA14EAE66D436166D11BE9B04516CA480E3E2C7936A647DA1BE721
    )

    env = Environment(
        fee_recipient=sender,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=18137262409615484,
    )

    pre[sender] = Account(balance=0x26551A696CACB206)
    # Source: raw
    # 0x62f46a4f547b169c9edf92f4b39273fe47accc75d1209ae58463c2585607ce051ff6714c4f0fbf6de0659784434fb240652ff52d08576408f168a43a6651f765a4788a05537086290691d5a3239db43eefea96b0012ea26534e99e4ba9ee7f92f37fa731707f800683bafb70815757d861ad8cc6804154ce5b9de3146b58cd53  # noqa: E501
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.SLOAD(key=0xF46A4F)
        + Op.JUMPI(
            pc=0x4C4F0FBF6DE0659784434FB240652FF52D08,
            condition=0x169C9EDF92F4B39273FE47ACCC75D1209AE58463C2585607CE051FF6,  # noqa: E501
        )
        + Op.MSTORE8(offset=0x51F765A4788A05, value=0x8F168A43A)
        + Op.PUSH17[0x86290691D5A3239DB43EEFEA96B0012EA2]
        + Op.MSTORE8(
            offset=0x92F37FA731707F800683BAFB70815757D861AD8CC6804154CE5B9DE3146B58CD,  # noqa: E501
            value=0x34E99E4BA9EE,
        ),
        balance=0x577686E8D1344340,
        nonce=112,
        address=Address(0x88F8BB676EB054B4F4788ABF1200CB51361038CF),  # noqa: E501
    )
    pre[addr_2] = Account(balance=0x11BAE0BB79D6A164, nonce=163)

    tx = Transaction(
        sender=sender,
        to=Address(0x0000000000000000000000000000000000000007),
        data=Bytes(
            "73ac858c3531a0d29ea7a15dfca264e244056b35816eb2fa5e8b941bb7e03e269017ca7b29556e2c50a4525c68460af5ba912653059274ec9907faed7f4ceacf55ed7b50228e7e26e7113d6751750964de40c9f5bb9f378e19edc3fd6ffd6af7ee7710107f382df318b8e1c707719add3db4b00892ddfba9f3e970c8aa9b41f208c53bf041556585635e6534916c5ec0ba7162ea7979164bb27d007c198e1e50cb945b54a4dca4ac110de1a1d47f43fa61c9a6e916d30c3e89695e77cb0da0bcea3bd98260927c609b5782488c5d7e06f07fc67aa5f1cb3c2d7ee74a4054d94e0108b3c962a00fb567a505e96a974f83567a74b898ddd6136e1e6634e4c85cb37db14f98d0080ac548e092928b6eee8d6863592d990f9298d7040cfa486e4e881b0f19eb06892d2185cc0b295d7f2669f00ac67c30de107cd324610a5af8bb29d11354783888e7b8ba5ab533f959729b6e25886d426bbf4cd00626cffbc0ec6beb6a62ae0d9e7166a6303d22036c2b3d45e88057940ada00938e"  # noqa: E501
        ),
        gas_limit=4901005,
        value=0xF5E5CC4B,
    )

    post = {
        sender: Account(storage={}, code=b"", nonce=1),
        addr: Account(storage={}, nonce=112),
        addr_2: Account(storage={}, code=b"", nonce=163),
    }

    state_test(env=env, pre=pre, post=post, tx=tx)
