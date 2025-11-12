"""
Test [EIP-198: MODEXP Precompile](https://eips.ethereum.org/EIPS/eip-198).

Tests the MODEXP precompile, located at address 0x0000..0005. Test cases
from the EIP are labelled with `EIP-198-caseX` in the test id.
"""

import pytest
from execution_testing import (
    Account,
    Alloc,
    Bytes,
    Environment,
    Op,
    StateTestFiller,
    Transaction,
    compute_create_address,
)
from execution_testing.base_types.base_types import (
    FixedSizeBytes,
)

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
        (
            ModExpInput(
                base="",
                exponent="",
                modulus="",
                declared_exponent_length=2**32,
                declared_modulus_length=1,
            ),
            ModExpOutput(returned_data="0x00", call_success=False),
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
        pytest.param(  # Note: This is the only test case which goes out-of-
            # gas.
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
        # different declared moduli lengths and parities
        *[
            pytest.param(
                ModExpInput(
                    base="1234",
                    exponent="234",
                    modulus="1000" if parity == "power2" else "1010",
                    declared_modulus_length=width,
                ),
                ModExpOutput(
                    returned_data=FixedSizeBytes[width](  # type: ignore
                        (
                            (0x1234**0x234)
                            % (
                                (0x1000 if parity == "power2" else 0x1010)
                                # declared `width` bitshifts modulus left.
                                << ((width - 2) * 8)
                            )
                        ),
                        left_padding=True,
                    )
                ),
                id=f"EIP-198-case1-mod-{parity}-declared-length-{width}-bytes",
            )
            for width in [64, 128, 256, 512]
            for parity in ["power2", "even"]
        ],
        # out of gas cases
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000008000000000000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-exponent-length-0x80000000-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000004000000000000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-exponent-length-0x40000000-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000002000000000000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-exponent-length-0x20000000-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000001000000000000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-exponent-length-0x10000000-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000080000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-modulus-length-0x80000020-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000040000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-modulus-length-0x40000020-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000020000020"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-modulus-length-0x20000020-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000000000040"
                "00000000000000000000000000000000000000000000000000000000ffffffff"
                "80"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            id="large-modulus-length-0xffffffff-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "fffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff9"
                "0000000000000000000000000000000000000000000000000000000000000001"
                "0000000000000000000000000000000000000000000000000000000000000001"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            # FIXME
            marks=pytest.mark.skip(
                reason=(
                    "EELS bug: U256 overflow in modexp pointer arithmetic "
                    "before Osaka - see "
                    "github.com/ethereum/execution-specs/issues/1465"
                )
            ),
            id="max-base-length-overflow-out-of-gas",
        ),
        pytest.param(
            Bytes(
                "ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffa0"
            ),
            ModExpOutput(
                call_success=False,
                returned_data="0000000000000000000000000000000000000000000000000000000000000000",
            ),
            # FIXME
            marks=pytest.mark.skip(
                reason=(
                    "EELS bug: U256 overflow in modexp pointer arithmetic "
                    "before Osaka - see "
                    "github.com/ethereum/execution-specs/issues/1465"
                )
            ),
            id="immunefi-38958-by-omik-overflow",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="52",
                modulus=8 * "ff" + 8 * "00",
            ),
            ModExpOutput(
                returned_data="e8ca816be3ddb8a1243d253d80487649",
            ),
            id="mod-16-even-ctz-8",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="83",
                modulus=8 * "ff" + 16 * "00",
            ),
            ModExpOutput(
                returned_data="b05147078624b9661557222e8610fb9986f829a99c2ede1b",
            ),
            id="mod-24-even-ctz-16",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="0100",
                modulus=16 * "ff" + 24 * "00",
            ),
            ModExpOutput(
                returned_data="4af58b4c59a562ee7345b3805ed8b417fed242815e55bc8375a205de07597d51"
                "d2105f2f0730f401",
            ),
            id="mod-40-even-ctz-24",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="0200",
                modulus=40 * "ff" + 32 * "00",
            ),
            ModExpOutput(
                returned_data="e33fcb0f1a5abfca90c5036512aca2cb657acf53b0e31fed3e122d5dec19ee8c"
                "2e60be065d0b77059483760fbd2a7e5335bd075f4d13ebbd7679ef1b4306890c"
                "1d660d1276f1e801",
            ),
            id="mod-72-even-ctz-32",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="0300",
                modulus=96 * "ff" + 40 * "00",
            ),
            ModExpOutput(
                returned_data="4059444789547ff685087bca8a144d32556b2251613171aa4cf05d8a005015d9"
                "b8408ba5f7c89595e76d925173cf80e552a856b1ce217c1f33940f8241e6adcf"
                "76b672c4935a40f4bb36410ee24654c114cd718bea878742c703dc5abddbdbfa"
                "17d12328a2a6bb9d6e80dc0bc224eef03128625977a1e2c1d189336e303567d7"
                "442488538f42dc01",
            ),
            id="mod-136-even-ctz-40",
        ),
        pytest.param(
            ModExpInput(
                base="03",
                exponent="0600",
                modulus=216 * "ff" + 48 * "00",
            ),
            ModExpOutput(
                returned_data="b2eb4387ee3ad0b4cfe1e05b3962718e2de238b02cc2c2ce80ae1a3c13ffe387"
                "2a5b829fc77634ec4b2d07f57862a019d4e7a3dc035851d60a4dabfed7bc5a2d"
                "44d5f7840e621678a3dbfeb9c37a78350e7f98e1440cc8d7d601be78db75e3ed"
                "79a1b5200f3290263da23ee75df076a34b600b670226e21aee2ccfaa51aa7ad2"
                "76b55e50ca6c4854070e5f115a377f2b4177fd5f3803408989454bf61789f4b1"
                "4241d7e0cf2606929f8d5da04c743e3b44a9d692e60bfcd077ab7cc8ad3d70ec"
                "eac9a053acb9f436612e986706f715c3580fbe4b0485724f9363912131c1dedb"
                "9706f4241afc62d706153951fe69b5b5b754d8301063494791b58250ebf50ad9"
                "a78f7be54b95b801",
            ),
            id="mod-264-even-ctz-48",
        ),
    ],
    ids=lambda param: param.__repr__(),  # only required to remove parameter
    # names (input/output)
)
def test_modexp(
    state_test: StateTestFiller,
    mod_exp_input: ModExpInput | Bytes,
    output: ModExpOutput,
    pre: Alloc,
) -> None:
    """Test the MODEXP precompile."""
    env = Environment()
    sender = pre.fund_eoa()

    account = pre.deploy_contract(
        # Store all CALLDATA into memory (offset 0)
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        # Store the returned CALL status (success = 1, fail = 0) into slot 0:
        + Op.SSTORE(
            0,
            # Setup stack to CALL into ModExp with the CALLDATA and CALL into
            # it (+ pop value)
            Op.CALL(Op.GAS(), 0x05, 0, 0, Op.CALLDATASIZE(), 0, 0),
        )
        # Store contract deployment code to deploy the returned data from
        # ModExp as contract code (16 bytes)
        + Op.MSTORE(
            0,
            (
                # Need to `ljust` this PUSH32 in order to ensure the code
                # starts in memory at offset 0 (memory right-aligns stack items
                # which are not 32 bytes)
                Op.PUSH32(
                    bytes(
                        Op.CODECOPY(0, 16, Op.SUB(Op.CODESIZE(), 16))
                        + Op.RETURN(0, Op.SUB(Op.CODESIZE, 16))
                    ).ljust(32, bytes(1))
                )
            ),
        )
        # RETURNDATACOPY the returned data from ModExp into memory (offset 16
        # bytes)
        + Op.RETURNDATACOPY(16, 0, Op.RETURNDATASIZE())
        # CREATE contract with the deployment code + the returned data from
        # ModExp
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
