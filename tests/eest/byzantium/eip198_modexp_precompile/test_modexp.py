"""
abstract: Test [EIP-198: MODEXP Precompile](https://eips.ethereum.org/EIPS/eip-198)
    Tests the MODEXP precompile, located at address 0x0000..0005. Test cases from the EIP are
    labelled with `EIP-198-caseX` in the test id.
"""

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Bytes,
    Environment,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

from .helpers import ModExpInput, ModExpOutput

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-198.md"
REFERENCE_SPEC_VERSION = "5c8f066acb210c704ef80c1033a941aa5374aac5"


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    ["mod_exp_input", "output"],
    [
        (
            ModExpInput(base="", exponent="", modulus="02"),
            ModExpOutput(returned_data="0x01"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="0002"),
            ModExpOutput(returned_data="0x0001"),
        ),
        (
            ModExpInput(base="00", exponent="00", modulus="02"),
            ModExpOutput(returned_data="0x01"),
        ),
        (
            ModExpInput(base="", exponent="01", modulus="02"),
            ModExpOutput(returned_data="0x00"),
        ),
        (
            ModExpInput(base="01", exponent="01", modulus="02"),
            ModExpOutput(returned_data="0x01"),
        ),
        (
            ModExpInput(base="02", exponent="01", modulus="03"),
            ModExpOutput(returned_data="0x02"),
        ),
        (
            ModExpInput(base="02", exponent="02", modulus="05"),
            ModExpOutput(returned_data="0x04"),
        ),
        (
            ModExpInput(base="", exponent="", modulus=""),
            ModExpOutput(returned_data="0x"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="00"),
            ModExpOutput(returned_data="0x00"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="01"),
            ModExpOutput(returned_data="0x00"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="0001"),
            ModExpOutput(returned_data="0x0000"),
        ),
        # Test cases from EIP 198.
        pytest.param(
            ModExpInput(
                base="03",
                exponent="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2e",
                modulus="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
            ),
            ModExpOutput(
                returned_data="0000000000000000000000000000000000000000000000000000000000000001",
            ),
            id="EIP-198-case1",
        ),
        pytest.param(
            ModExpInput(
                base="",
                exponent="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2e",
                modulus="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
            ),
            ModExpOutput(
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="EIP-198-case2",
        ),
        pytest.param(  # Note: This is the only test case which goes out-of-gas.
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000020"
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"
                "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="EIP-198-case3-raw-input-out-of-gas",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="ffff",
                modulus="8000000000000000000000000000000000000000000000000000000000000000",
                extra_data="07",
            ),
            ModExpOutput(
                returned_data="0x3b01b01ac41f2d6e917c6d6a221ce793802469026d9ab7578fa2e79e4da6aaab",
            ),
            id="EIP-198-case4-extra-data_07",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000000000002"
                "0000000000000000000000000000000000000000000000000000000000000020"
                "03"
                "ffff"
                "80"
            ),
            ModExpOutput(
                returned_data="0x3b01b01ac41f2d6e917c6d6a221ce793802469026d9ab7578fa2e79e4da6aaab",
            ),
            id="EIP-198-case5-raw-input",
        ),
    ],
    ids=lambda param: param.__repr__(),  # only required to remove parameter names (input/output)
)
def test_modexp(
    state_test: StateTestFiller,
    mod_exp_input: ModExpInput | Bytes,
    output: ModExpOutput,
    pre: Alloc,
):
    """Test the MODEXP precompile."""
    env = Environment()
    sender = pre.fund_eoa()

    account = pre.deploy_contract(
        # Store all CALLDATA into memory (offset 0)
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        # Store the returned CALL status (success = 1, fail = 0) into slot 0:
        + Op.SSTORE(
            0,
            # Setup stack to CALL into ModExp with the CALLDATA and CALL into it (+ pop value)
            Op.CALL(Op.GAS(), 0x05, 0, 0, Op.CALLDATASIZE(), 0, 0),
        )
        # Store contract deployment code to deploy the returned data from ModExp as
        # contract code (16 bytes)
        + Op.MSTORE(
            0,
            (
                # Need to `ljust` this PUSH32 in order to ensure the code starts
                # in memory at offset 0 (memory right-aligns stack items which are not
                # 32 bytes)
                Op.PUSH32(
                    bytes(
                        Op.CODECOPY(0, 16, Op.SUB(Op.CODESIZE(), 16))
                        + Op.RETURN(0, Op.SUB(Op.CODESIZE, 16))
                    ).ljust(32, bytes(1))
                )
            ),
        )
        # RETURNDATACOPY the returned data from ModExp into memory (offset 16 bytes)
        + Op.RETURNDATACOPY(16, 0, Op.RETURNDATASIZE())
        # CREATE contract with the deployment code + the returned data from ModExp
        + Op.CREATE(0, 0, Op.ADD(16, Op.RETURNDATASIZE()))
        # STOP (handy for tracing)
        + Op.STOP(),
    )

    tx = Transaction(
        ty=0x0,
        to=account,
        data=mod_exp_input,
        gas_limit=500_000,
        protected=True,
        sender=sender,
    )

    post = {}
    if output.call_success:
        contract_address = compute_create_address(address=account, nonce=1)
        post[contract_address] = Account(code=output.returned_data)
    post[account] = Account(storage={0: output.call_success})

    state_test(env=env, pre=pre, post=post, tx=tx)
