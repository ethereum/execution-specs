"""test `CALLDATASIZE` opcode."""

import pytest

from ethereum_test_forks import Byzantium, Fork
from ethereum_test_tools import Account, Alloc, StateTestFiller, Transaction
from ethereum_test_tools import Macros as Om
from ethereum_test_tools.vm.opcode import Opcodes as Op


@pytest.mark.ported_from(
    [
        "https://github.com/ethereum/tests/blob/v13.3/src/GeneralStateTestsFiller/VMTests/vmTests/calldatasizeFiller.yml",
    ],
    pr=["https://github.com/ethereum/execution-spec-tests/pull/1236"],
)
@pytest.mark.parametrize(
    "args_size",
    [0, 2, 16, 33, 257],
)
@pytest.mark.parametrize("calldata_source", ["contract", "tx"])
def test_calldatasize(
    state_test: StateTestFiller,
    fork: Fork,
    args_size: int,
    pre: Alloc,
    calldata_source: str,
):
    """
    Test `CALLDATASIZE` opcode.

    Tests two scenarios:
    - calldata_source is "contract": CALLDATASIZE reads from calldata passed by another contract
    - calldata_source is "tx": CALLDATASIZE reads directly from transaction calldata

    Based on https://github.com/ethereum/tests/blob/81862e4848585a438d64f911a19b3825f0f4cd95/src/GeneralStateTestsFiller/VMTests/vmTests/calldatasizeFiller.yml
    """
    contract_address = pre.deploy_contract(Op.SSTORE(key=0x0, value=Op.CALLDATASIZE))
    calldata = b"\x01" * args_size

    if calldata_source == "contract":
        to = pre.deploy_contract(
            code=(
                Om.MSTORE(calldata, 0x0)
                + Op.CALL(
                    gas=Op.SUB(Op.GAS(), 0x100),
                    address=contract_address,
                    value=0x0,
                    args_offset=0x0,
                    args_size=args_size,
                    ret_offset=0x0,
                    ret_size=0x0,
                )
            )
        )

        tx = Transaction(
            gas_limit=100_000,
            protected=fork >= Byzantium,
            sender=pre.fund_eoa(),
            to=to,
        )

    else:
        tx = Transaction(
            data=calldata,
            gas_limit=100_000,
            protected=fork >= Byzantium,
            sender=pre.fund_eoa(),
            to=contract_address,
        )

    post = {contract_address: Account(storage={0x00: args_size})}
    state_test(pre=pre, post=post, tx=tx)
