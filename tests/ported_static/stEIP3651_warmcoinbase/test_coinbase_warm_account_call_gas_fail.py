"""
Test_coinbase_warm_account_call_gas_fail.

Ported from:
state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml
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
    [
        "state_tests/Shanghai/stEIP3651_warmcoinbase/coinbaseWarmAccountCallGasFailFiller.yml"  # noqa: E501
    ],
)
@pytest.mark.valid_from("Cancun")
@pytest.mark.parametrize(
    "d, g, v",
    [
        pytest.param(
            0,
            0,
            0,
            id="d0",
        ),
        pytest.param(
            1,
            0,
            0,
            id="d1",
        ),
        pytest.param(
            2,
            0,
            0,
            id="d2",
        ),
        pytest.param(
            3,
            0,
            0,
            id="d3",
        ),
    ],
)
@pytest.mark.pre_alloc_mutable
def test_coinbase_warm_account_call_gas_fail(
    state_test: StateTestFiller,
    pre: Alloc,
    fork: Fork,
    d: int,
    g: int,
    v: int,
) -> None:
    """Test_coinbase_warm_account_call_gas_fail."""
    coinbase = Address(0x50228C44ED92561D94511E8518A75AA463BD444B)
    sender = EOA(
        key=0x48DC5A9F099CAAAA557742CA3A990A94BE45B9969126A1BC74E5E8BE5A2B5B47
    )

    env = Environment(
        fee_recipient=coinbase,
        number=1,
        timestamp=1000,
        prev_randao=0x20000,
        base_fee_per_gas=10,
        gas_limit=100000000,
    )

    pre[coinbase] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    pre[sender] = Account(balance=0xBA1A9CE0BA1A9CE, nonce=1)
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(call(0, cb, 0, 0, 0, 0, 0))
    # }
    addr = pre.deploy_contract(  # noqa: F841
        code=Op.CALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x8DDF5D9A5251C41EFD2949F53DB0A464116C7C6E),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(callcode(0, cb, 0, 0, 0, 0, 0))
    # }
    addr_2 = pre.deploy_contract(  # noqa: F841
        code=Op.CALLCODE(
            gas=Op.DUP2,
            address=Op.COINBASE,
            value=Op.DUP1,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x498516B6B2F25CB6A8E011A7C37A617B77E7D500),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(delegatecall(0, cb, 0, 0, 0, 0))
    # }
    addr_3 = pre.deploy_contract(  # noqa: F841
        code=Op.DELEGATECALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x8873820BB96DAA39DB93AE64A9D6397E4C6A48D7),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    let cb := coinbase()
    #    pop(staticcall(0, cb, 0, 0, 0, 0))
    # }
    addr_4 = pre.deploy_contract(  # noqa: F841
        code=Op.STATICCALL(
            gas=Op.DUP2,
            address=Op.COINBASE,
            args_offset=Op.DUP1,
            args_size=Op.DUP1,
            ret_offset=Op.DUP1,
            ret_size=0x0,
        )
        + Op.STOP,
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x303B6790D019874A107418EB549E4E7766A64728),  # noqa: E501
    )
    # Source: yul
    # berlin
    # {
    #    // Depending on the called contract here, the subcall will perform
    #    // another call/delegatecall/staticcall/callcode that will only succeed  # noqa: E501
    #    // if coinbase is considered warm by default (post-Shanghai).
    #    let calladdr := calldataload(4)
    #
    #    let callgas := 100
    #    switch calladdr
    #    case <contract:0x0000000000000000000000000000000000001000> {
    #      // Extra: COINBASE + 6xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 27)
    #    }
    #    case <contract:0x0000000000000000000000000000000000002000> {
    #      // Extra: COINBASE + 6xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 27)
    #    }
    #    case <contract:0x0000000000000000000000000000000000003000> {
    #      // Extra: COINBASE + 5xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 24)
    #    }
    #    case <contract:0x0000000000000000000000000000000000004000> {
    #      // Extra: COINBASE + 5xPUSH1 + DUP6 + 2xPOP
    #      callgas := add(callgas, 24)
    #    }
    #    // Call and save result
    #    sstore(0, call(callgas, calladdr, 0, 0, 0, 0, 0))
    #
    # }
    target = pre.deploy_contract(  # noqa: F841
        code=Op.PUSH1[0x0]
        + Op.DUP1 * 4
        + Op.CALLDATALOAD(offset=0x4)
        + Op.PUSH1[0x64]
        + Op.DUP2
        + Op.JUMPI(
            pc=0x88,
            condition=Op.EQ(
                0x8DDF5D9A5251C41EFD2949F53DB0A464116C7C6E, Op.DUP1
            ),
        )
        + Op.JUMPI(
            pc=0x88,
            condition=Op.EQ(
                0x498516B6B2F25CB6A8E011A7C37A617B77E7D500, Op.DUP1
            ),
        )
        + Op.JUMPI(
            pc=0x80,
            condition=Op.EQ(
                0x8873820BB96DAA39DB93AE64A9D6397E4C6A48D7, Op.DUP1
            ),
        )
        + Op.PUSH20[0x303B6790D019874A107418EB549E4E7766A64728]
        + Op.JUMPI(pc=0x79, condition=Op.EQ)
        + Op.JUMPDEST
        + Op.SSTORE(key=0x0, value=Op.CALL)
        + Op.STOP
        + Op.JUMPDEST
        + Op.PUSH1[0x18]
        + Op.ADD
        + Op.JUMP(pc=0x73)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x18]
        + Op.ADD
        + Op.JUMP(pc=0x73)
        + Op.JUMPDEST
        + Op.POP
        + Op.PUSH1[0x1B]
        + Op.ADD
        + Op.JUMP(pc=0x73),
        balance=0xBA1A9CE0BA1A9CE,
        nonce=1,
        address=Address(0x0A92FC97BB4C47B3D5E9E96FBB1C3FC2F07DBA81),  # noqa: E501
    )

    tx_data = [
        Bytes("693c6139") + Hash(addr, left_padding=True),
        Bytes("693c6139") + Hash(addr_2, left_padding=True),
        Bytes("693c6139") + Hash(addr_3, left_padding=True),
        Bytes("693c6139") + Hash(addr_4, left_padding=True),
    ]
    tx_gas = [80000]

    tx = Transaction(
        sender=sender,
        to=target,
        data=tx_data[d],
        gas_limit=tx_gas[g],
        nonce=1,
    )

    post = {target: Account(storage={0: 1})}

    state_test(env=env, pre=pre, post=post, tx=tx)
