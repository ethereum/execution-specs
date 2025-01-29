"""
abstract: Tests [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152)
    Test cases for [EIP-152: BLAKE2b compression precompile](https://eips.ethereum.org/EIPS/eip-152).
"""

from dataclasses import dataclass

import pytest

from ethereum_test_tools import (
    Account,
    Alloc,
    Environment,
    StateTestFiller,
    TestParameterGroup,
    Transaction,
)
from ethereum_test_tools.vm.opcode import Opcodes as Op

REFERENCE_SPEC_GIT_PATH = "EIPS/eip-152.md"
REFERENCE_SPEC_VERSION = "5510973b40973b6aa774f04c9caba823c8ff8460"


@dataclass(kw_only=True, frozen=True, repr=False)
class Blake2bInput(TestParameterGroup):
    """
    Helper class that defines the BLAKE2b precompile inputs and creates the
    call data from them. Returns all inputs encoded as bytes.

    Attributes:
        rounds_length (int): An optional integer representing the bytes length
            for the number of rounds. Defaults to the expected length of 4.
        rounds (int | str): A hex string or integer value representing the number of rounds.
        h (str): A hex string that represents the state vector.
        m (str): A hex string that represents the message block vector.
        t_0 (int | str): A hex string or integer value that represents the first offset counter.
        t_1 (int | str): A hex string or integer value that represents the second offset counter.
        f (bool): An optional boolean that represents the final block indicator flag.
            Defaults to True.

    """

    rounds_length: int = 4
    rounds: int | str
    h: str
    m: str
    t_0: int | str
    t_1: int | str
    f: bool | int = True

    def create_blake2b_tx_data(self):
        """Generate input for the BLAKE2b precompile."""
        _rounds = self.rounds.to_bytes(length=self.rounds_length, byteorder="big")
        _h = bytes.fromhex(self.h)
        _m = bytes.fromhex(self.m)
        _t_0 = (
            bytes.fromhex(self.t_0)
            if isinstance(self.t_0, str)
            else self.t_0.to_bytes(length=8, byteorder="little")
        )
        _t_1 = (
            bytes.fromhex(self.t_1)
            if isinstance(self.t_1, str)
            else self.t_1.to_bytes(length=8, byteorder="little")
        )
        _f = int(self.f).to_bytes(length=1, byteorder="big")

        return _rounds + _h + _m + _t_0 + _t_1 + _f


@dataclass(kw_only=True, frozen=True, repr=False)
class ExpectedOutput(TestParameterGroup):
    """
    Expected test result.

    Attributes:
        call_succeeds (str | bool): A hex string or boolean to indicate whether the call was
            successful or not.
        data_1 (str): String value of the first updated state vector.
        data_2 (str): String value of the second updated state vector.

    """

    call_succeeds: str | bool
    data_1: str
    data_2: str


@pytest.mark.valid_from("Istanbul")
@pytest.mark.parametrize(
    ["data", "output"],
    [
        pytest.param(
            Blake2bInput(
                rounds=0,
                rounds_length=0,
                h="",
                m="",
                t_0="",
                t_1="",
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case0",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=3,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case1",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                rounds_length=5,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case2",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
                f=2,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-case3",
        ),
        pytest.param(
            Blake2bInput(
                rounds=0,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x08c9bcf367e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5",
                data_2="0xd282e6ad7f520e511f6c3e2b8c68059b9442be0454267ce079217e1319cde05b",
            ),
            id="EIP-152-case4",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xba80a53f981c4d0d6a2797b69f12f6e94c212f14685ac4b74b12bb6fdbffa2d1",
                data_2="0x7d87c5392aab792dc252d5de4533cc9518d38aa8dbf1925ab92386edd4009923",
            ),
            id="EIP-152-case5",
        ),
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
                f=False,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x75ab69d3190a562c51aef8d88f1c2775876944407270c42c9844252c26d28752",
                data_2="0x98743e7f6d5ea2f2d3e8d226039cd31b4e426ac4f2d3d666a610c2116fde4735",
            ),
            id="EIP-152-case6",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xb63a380cb2897d521994a85234ee2c181b5f844d2c624c002677e9703449d2fb",
                data_2="0xa551b3a8333bcdf5f2f7e08993d53923de3d64fcc68c034e717b9293fed7a421",
            ),
            id="EIP-152-case7",
        ),
        # Excessive number of rounds expects to run out of gas
        pytest.param(
            Blake2bInput(
                rounds=4294967295,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x0",
                data_2="0x0",
            ),
            id="EIP-152-case8",
        ),
        # Case from https://github.com/ethereum/tests/pull/948#issuecomment-925964632
        pytest.param(
            Blake2bInput(
                rounds=12,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=5,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xf3e89a60ec4b0b1854744984e421d22b82f181bd4601fb9b1726b2662da61c29",
                data_2="0xdff09e75814acb2639fd79e56616e55fc135f8476f0302b3dc8d44e082eb83a8",
            ),
            id="EIP-152-case9",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa8ef8236e5f48a74af375df15681d128457891c1cc4706f30747b2d40300b2f4",
                data_2="0x9d19f80fbd0945fd87736e1fc1ff10a80fd85a7aa5125154f3aaa3789ddff673",
            ),
            id="EIP-152-0016",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xbc5e888ed71b546da7b1506179bdd6c184a6410c40de33f9c330207417797889",
                data_2="0x5dbe74144468aefe5c2afce693c62dbca99e5e076dd467fe90a41278b16d691e",
            ),
            id="EIP-152-0032",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x74097ae7b16ffd18c742aee5c55dc89d54b6f1a8a19e6139ccfb38afba56b6b0",
                data_2="0x2cc35c441c19c21194fefb6841e72202f7c9d05eb9c3cfd8f94c67aa77d473c1",
            ),
            id="EIP-152-0064",
        ),
        pytest.param(
            Blake2bInput(
                rounds=128,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xd82c6a670dc90af9d7f77644eacbeddfed91b760c65c927871784abceaab3f81",
                data_2="0x3759733a1736254fb1cfc515dbfee467930955af56e27ee435f836fc3e65969f",
            ),
            id="EIP-152-0128",
        ),
        pytest.param(
            Blake2bInput(
                rounds=256,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5d6ff04d5ebaee5687d634613ab21e9a7d36f782033c74f91d562669aaf9d592",
                data_2="0xc86346cb2df390243a952834306b389e656876a67934e2c023bce4918a016d4e",
            ),
            id="EIP-152-0256",
        ),
        pytest.param(
            Blake2bInput(
                rounds=512,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa2c1eb780a6e1249156fe0751e5d4687ea9357b0651c78df660ab004cb477363",
                data_2="0x6298bbbc683e4a0261574b6d857a6a99e06b2eea50b16f86343d2625ff222b98",
            ),
            id="EIP-152-0512",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1024,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162630000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=3,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x689419d2bf32b5a9901a2c733b9946727026a60d8773117eabb35f04a52cdcf1",
                data_2="0xb8fb4473454cf03d46c36a10b3f784aae4dc80a24424960e66a8ad5a8c2bfb30",
            ),
            id="EIP-152-1024",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x4ab6df9d1f57140bbd27b5e164f42102d9e2b0bf4d53da501273f81a37e505c7",
                data_2="0xf6e136f9ca4b693aa6e990b04c6412296dc09540c23c395f183011a0c5d7392e",
            ),
            id="EIP-152-0016-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x7af9b4f9c25ba3e3fd4fcb957e703b7b2e648990fe8e24c6ca2a2dfac4ce76e6",
                data_2="0x18acffc26913d6759843362adeb4c95299777baaa977b5d94dd219d1777e4cb",
            ),
            id="EIP-152-0032-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x97eb79f7abc085a3da64d6e8643d196cbf522a51985ba2cc6a7ca14289b59df0",
                data_2="0x73366eb68e41966eb8b33ab5bd6078d0de2fa4edc986b1d2afc4c92f2fc30cda",
            ),
            id="EIP-152-0064-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=128,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5ef3d6ee148936390a9053e91ab5a92f4de4dfc62ebb95d71485be26d9b78c8d",
                data_2="0x8989dfe319f2fb5f11784174db63a7bcfc50de04e13fad57bea159e46e8811df",
            ),
            id="EIP-152-0128-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=256,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xa36be13275fec9a91779f0c9b06b1b40d8c8a13ab0786d0764c2eb708cc8eb81",
                data_2="0xf1acb2a3c7abd2ff5a9fdfe88b81f6f56288dc5260a9c810f023ae83b9b64a1a",
            ),
            id="EIP-152-0256-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=512,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xc987e560e3f90833c0d10ae1282bd9d35a7ba06d8abaa13a994d0962ed2bbaa9",
                data_2="0xf69c1e1e7c9aedb75e72d1b46e9f1b2ad8f8c2f7f858a04ed8aec16f964a96da",
            ),
            id="EIP-152-0512-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=1024,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f7000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000",
                t_0=16,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x224138a6afa847230ff09c23e2ca66522e22d26884b09d7740e2dd127cb61057",
                data_2="0x90cecbd4de6a52a733ca4a59583c064ad6ec7653d5d457b681de332f16f3d45",
            ),
            id="EIP-152-1024-16",
        ),
        pytest.param(
            Blake2bInput(
                rounds=16,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0xabcd200f2962ede252fc455ea70d12b236ad2f4046b91e17558a7741d9da39a2",
                data_2="0x548083b610bb8591ca50418eabd15b6489a936b178a435b4c182ffa475eba4d8",
            ),
            id="EIP-152-0016-120",
        ),
        pytest.param(
            Blake2bInput(
                rounds=32,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x39fc2077154fba422b3d628d10908c596beebea8dfd90f14566aec4f60bdb2bc",
                data_2="0xa75d73ab2b224d58c3568cbc7fc8905cc849f10745f00addef02384032d53729",
            ),
            id="EIP-152-0032-120",
        ),
        pytest.param(
            Blake2bInput(
                rounds=64,
                h="48c9bdf267e6096a3ba7ca8485ae67bb2bf894fe72f36e3cf1361d5f3af54fa5d182e6ad7f520e511f6c3e2b8c68059b6bbd41fbabd9831f79217e1319cde05b",
                m="6162636465666768696a6b6c6d6e6f707172737475767778797a7b7c7d7e7f808182838485868788898a8b8c8d8e8f909192939495969798999a9b9c9d9e9fa0a1a2a3a4a5a6a7a8a9aaabacadaeafb0b1b2b3b4b5b6b7b8b9babbbcbdbebfc0c1c2c3c4c5c6c7c8c9cacbcccdcecfd0d1d2d3d4d5d6d7d8d900000000000000",
                t_0=120,
                t_1=0,
            ),
            ExpectedOutput(
                call_succeeds=True,
                data_1="0x5bb981381beb687d5fdbe5e7c096fbd1ce193b780948c1d74ebbb7c58db364c7",
                data_2="0xb7695d32f918444dbdcbdcff476fc70a926e228c4cbb7d05473711d3b56e5b33",
            ),
            id="EIP-152-0064-120",
        ),
        pytest.param(
            Blake2bInput(
                rounds=0,
                rounds_length=0,
                h="00",
                m="00",
                t_0=0,
                t_1=0,
                f=0,
            ),
            ExpectedOutput(
                call_succeeds=False,
                data_1="0x00",
                data_2="0x00",
            ),
            id="EIP-152-RFC-7693-zero-input",
        ),
    ],
)
def test_blake2b(
    state_test: StateTestFiller,
    data: Blake2bInput,
    output: ExpectedOutput,
    pre: Alloc,
):
    """Test BLAKE2b precompile."""
    env = Environment()

    account = pre.deploy_contract(
        # Store all CALLDATA into memory (offset 0)
        Op.CALLDATACOPY(0, 0, Op.CALLDATASIZE())
        # Store the returned CALL status (success = 1, fail = 0) into slot 0:
        + Op.SSTORE(
            0,
            # Setup stack to CALL into Blake2b with the CALLDATA and CALL into it (+ pop value)
            Op.CALL(
                address=9,
                args_offset=0,
                args_size=Op.CALLDATASIZE(),
                ret_offset=0x200,
                ret_size=0x40,
                gas_limit=1_000_000,
            ),
        )
        + Op.SSTORE(
            1,
            Op.MLOAD(0x200),
        )
        + Op.SSTORE(
            2,
            Op.MLOAD(0x220),
        )
        + Op.STOP(),
        storage={0: 0xDEADBEEF},
    )
    sender = pre.fund_eoa()

    tx = Transaction(
        ty=0x0,
        to=account,
        data=data.create_blake2b_tx_data(),
        gas_limit=1_000_000,
        protected=True,
        sender=sender,
        value=100000,
    )

    post = {
        account: Account(
            storage={
                0: 0x1 if output.call_succeeds else 0x0,
                1: output.data_1,
                2: output.data_2,
            }
        )
    }
    state_test(env=env, pre=pre, post=post, tx=tx)
