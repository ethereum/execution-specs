"""
abstract: Test [EIP-198: MODEXP Precompile](https://eips.ethereum.org/EIPS/eip-198)
    Tests the MODEXP precompile, located at address 0x0000..0005. Test cases from the EIP are
    labelled with `EIP-198-caseX` in the test id.
"""
from dataclasses import dataclass

import pytest

from ethereum_test_tools import (
    Account,
    Address,
    Environment,
    StateTestFiller,
    TestAddress,
    TestParameterGroup,
    Transaction,
    compute_create_address,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-198.md"
REFERENCE_SPEC_VERSION = "9e393a79d9937f579acbdcb234a67869259d5a96"


@dataclass(kw_only=True, frozen=True, repr=False)
class ModExpInput(TestParameterGroup):
    """
    Helper class that defines the MODEXP precompile inputs and creates the
    call data from them.

    Attributes:
        base (str): The base value for the MODEXP precompile.
        exponent (str): The exponent value for the MODEXP precompile.
        modulus (str): The modulus value for the MODEXP precompile.
        extra_data (str): Defines extra padded data to be added at the end of the calldata
            to the precompile. Defaults to an empty string.
    """

    base: str
    exponent: str
    modulus: str
    extra_data: str = ""

    def create_modexp_tx_data(self):
        """
        Generates input for the MODEXP precompile.
        """
        return (
            "0x"
            + f"{int(len(self.base)/2):x}".zfill(64)
            + f"{int(len(self.exponent)/2):x}".zfill(64)
            + f"{int(len(self.modulus)/2):x}".zfill(64)
            + self.base
            + self.exponent
            + self.modulus
            + self.extra_data
        )


@dataclass(kw_only=True, frozen=True, repr=False)
class ModExpRawInput(TestParameterGroup):
    """
    Helper class to directly define a raw input to the MODEXP precompile.
    """

    raw_input: str

    def create_modexp_tx_data(self):
        """
        The raw input is already the MODEXP precompile input.
        """
        return self.raw_input


@dataclass(kw_only=True, frozen=True, repr=False)
class ExpectedOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
        call_return_code (str): The return_code from CALL, 0 indicates unsuccessful call
            (out-of-gas), 1 indicates call succeeded.
        returned_data (str): The output returnData is the expected output of the call
    """

    call_return_code: str
    returned_data: str


@pytest.mark.valid_from("Byzantium")
@pytest.mark.parametrize(
    ["input", "output"],
    [
        (
            ModExpInput(base="", exponent="", modulus="02"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x01"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="0002"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x0001"),
        ),
        (
            ModExpInput(base="00", exponent="00", modulus="02"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x01"),
        ),
        (
            ModExpInput(base="", exponent="01", modulus="02"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x00"),
        ),
        (
            ModExpInput(base="01", exponent="01", modulus="02"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x01"),
        ),
        (
            ModExpInput(base="02", exponent="01", modulus="03"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x02"),
        ),
        (
            ModExpInput(base="02", exponent="02", modulus="05"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x04"),
        ),
        (
            ModExpInput(base="", exponent="", modulus=""),
            ExpectedOutput(call_return_code="0x01", returned_data="0x"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="00"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x00"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="01"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x00"),
        ),
        (
            ModExpInput(base="", exponent="", modulus="0001"),
            ExpectedOutput(call_return_code="0x01", returned_data="0x0000"),
        ),
        # Test cases from EIP 198.
        pytest.param(
            ModExpInput(
                base="03",
                exponent="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2e",
                modulus="fffffffffffffffffffffffffffffffffffffffffffffffffffffffefffffc2f",
            ),
            ExpectedOutput(
                call_return_code="0x01",
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
            ExpectedOutput(
                call_return_code="0x01",
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="EIP-198-case2",
        ),
        pytest.param(  # Note: This is the only test case which goes out-of-gas.
            ModExpRawInput(
                raw_input="0000000000000000000000000000000000000000000000000000000000000000"
                "0000000000000000000000000000000000000000000000000000000000000020"
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff"
                "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffe"
                "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffd"
            ),
            ExpectedOutput(
                call_return_code="0x00",
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
            ExpectedOutput(
                call_return_code="0x01",
                returned_data="0x3b01b01ac41f2d6e917c6d6a221ce793802469026d9ab7578fa2e79e4da6aaab",
            ),
            id="EIP-198-case4-extra-data_07",
        ),
        pytest.param(
            ModExpRawInput(
                raw_input="0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000000000002"
                "0000000000000000000000000000000000000000000000000000000000000020"
                "03"
                "ffff"
                "80"
            ),
            ExpectedOutput(
                call_return_code="0x01",
                returned_data="0x3b01b01ac41f2d6e917c6d6a221ce793802469026d9ab7578fa2e79e4da6aaab",
            ),
            id="EIP-198-case5-raw-input",
        ),
    ],
    ids=lambda param: param.__repr__(),  # only required to remove parameter names (input/output)
)
def test_modexp(state_test: StateTestFiller, input: ModExpInput, output: ExpectedOutput):
    """
    Test the MODEXP precompile
    """
    env = Environment()
    pre = {TestAddress: Account(balance=1000000000000000000000)}

    account = Address(0x100)

    pre[account] = Account(
        code=(
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
                    (
                        # Need to `ljust` this PUSH32 in order to ensure the code starts
                        # in memory at offset 0 (memory right-aligns stack items which are not
                        # 32 bytes)
                        Op.PUSH32(
                            (
                                Op.CODECOPY(0, 16, Op.SUB(Op.CODESIZE(), 16))
                                + Op.RETURN(0, Op.SUB(Op.CODESIZE, 16))
                            ).ljust(32, bytes(1))
                        )
                    )
                ),
            )
            # RETURNDATACOPY the returned data from ModExp into memory (offset 16 bytes)
            + Op.RETURNDATACOPY(16, 0, Op.RETURNDATASIZE())
            # CREATE contract with the deployment code + the returned data from ModExp
            + Op.CREATE(0, 0, Op.ADD(16, Op.RETURNDATASIZE()))
            # STOP (handy for tracing)
            + Op.STOP()
        )
    )

    tx = Transaction(
        ty=0x0,
        nonce=0,
        to=account,
        data=input.create_modexp_tx_data(),
        gas_limit=500000,
        gas_price=10,
        protected=True,
    )

    post = {}
    if output.call_return_code != "0x00":
        contract_address = compute_create_address(account, tx.nonce)
        post[contract_address] = Account(code=output.returned_data)
    post[account] = Account(storage={0: output.call_return_code})

    state_test(env=env, pre=pre, post=post, tx=tx)
