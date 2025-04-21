"""Expect section structure of ethereum/tests fillers."""

from enum import Enum
from typing import Dict, List, Literal, Union

from pydantic import BaseModel, Field, ValidationInfo, field_validator

from ethereum_test_base_types import CamelModel
from ethereum_test_exceptions import TransactionExceptionInstanceOrList
from ethereum_test_forks import get_forks

from .common import AddressInFiller, CodeInFiller, ValueInFiller


class Indexes(BaseModel):
    """Class that represents an index filler."""

    data: int | List[Union[int, str]] | List[int] | str = Field(-1)
    gas: int | List[Union[int, str]] | List[int] | str = Field(-1)
    value: int | List[Union[int, str]] | List[int] | str = Field(-1)

    class Config:
        """Model Config."""

        extra = "forbid"


class AccountInExpectSection(BaseModel):
    """Class that represents an account in expect section filler."""

    balance: ValueInFiller | None = Field(None)
    code: CodeInFiller | None = Field(None)
    nonce: ValueInFiller | None = Field(None)
    storage: Dict[ValueInFiller, ValueInFiller | Literal["ANY"]] | None = Field(None)
    expected_to_not_exist: str | int | None = Field(None, alias="shouldnotexist")

    class Config:
        """Model Config."""

        extra = "forbid"


class CMP(Enum):
    """Comparison action."""

    GT = 1
    LT = 2
    LE = 3
    GE = 4
    EQ = 5


def parse_networks(fork_with_operand: str) -> List[str]:
    """Parse fork_with_operand `>=Cancun` into [Cancun, Prague, ...]."""
    parsed_forks: List[str] = []
    all_forks_by_name = [fork.name() for fork in get_forks()]

    action: CMP = CMP.EQ
    fork: str = fork_with_operand
    if fork_with_operand[:1] == "<":
        action = CMP.LT
        fork = fork_with_operand[1:]
    if fork_with_operand[:1] == ">":
        action = CMP.GT
        fork = fork_with_operand[1:]
    if fork_with_operand[:2] == "<=":
        action = CMP.LE
        fork = fork_with_operand[2:]
    if fork_with_operand[:2] == ">=":
        action = CMP.GE
        fork = fork_with_operand[2:]

    if action == CMP.EQ:
        fork = fork_with_operand

    # translate unsupported fork names
    if fork == "EIP158":
        fork = "Byzantium"

    if action == CMP.EQ:
        parsed_forks.append(fork)
        return parsed_forks

    try:
        print(all_forks_by_name)
        idx = all_forks_by_name.index(fork)
        # ['Frontier', 'Homestead', 'Byzantium', 'Constantinople', 'ConstantinopleFix',
        #  'Istanbul', 'MuirGlacier', 'Berlin', 'London', 'ArrowGlacier', 'GrayGlacier',
        #  'Paris', 'Shanghai', 'Cancun', 'Prague', 'Osaka']
    except ValueError:
        raise ValueError(f"Unsupported fork: {fork}") from Exception

    if action == CMP.GE:
        parsed_forks = all_forks_by_name[idx:]
    elif action == CMP.GT:
        parsed_forks = all_forks_by_name[idx + 1 :]
    elif action == CMP.LE:
        parsed_forks = all_forks_by_name[: idx + 1]
    elif action == CMP.LT:
        parsed_forks = all_forks_by_name[:idx]

    return parsed_forks


class ExpectSectionInStateTestFiller(CamelModel):
    """Expect section in state test filler."""

    indexes: Indexes = Field(default_factory=Indexes)
    network: List[str]
    result: Dict[AddressInFiller, AccountInExpectSection]
    expect_exception: Dict[str, TransactionExceptionInstanceOrList] | None = None

    class Config:
        """Model Config."""

        extra = "forbid"

    @field_validator("network", mode="before")
    @classmethod
    def parse_networks(cls, network: List[str], info: ValidationInfo) -> List[str]:
        """Parse networks into array of forks."""
        forks: List[str] = []
        for net in network:
            forks.extend(parse_networks(net))
        return forks

    @field_validator("expect_exception", mode="before")
    @classmethod
    def parse_expect_exception(
        cls, expect_exception: Dict[str, str] | None, info: ValidationInfo
    ) -> Dict[str, str] | None:
        """Parse operand networks in exceptions."""
        if expect_exception is None:
            return expect_exception

        parsed_expect_exception: Dict[str, str] = {}
        for fork_with_operand, exception in expect_exception.items():
            forks: List[str] = parse_networks(fork_with_operand)
            for fork in forks:
                if fork in parsed_expect_exception:
                    raise ValueError(
                        "Expect exception has redundant fork with multiple exceptions!"
                    )
                parsed_expect_exception[fork] = exception

        return parsed_expect_exception

    def has_index(self, d: int, g: int, v: int) -> bool:
        """Check if there is index set in indexes."""
        d_match: bool = False
        g_match: bool = False
        v_match: bool = False

        # Check if data index match
        if isinstance(self.indexes.data, int):
            d_match = True if self.indexes.data == -1 or self.indexes.data == d else False
        elif isinstance(self.indexes.data, list):
            d_match = True if self.indexes.data.count(d) else False

        # Check if gas index match
        if isinstance(self.indexes.gas, int):
            g_match = True if self.indexes.gas == -1 or self.indexes.gas == g else False
        elif isinstance(self.indexes.gas, list):
            g_match = True if self.indexes.gas.count(g) else False

        # Check if value index match
        if isinstance(self.indexes.value, int):
            v_match = True if self.indexes.value == -1 or self.indexes.value == v else False
        elif isinstance(self.indexes.value, list):
            v_match = True if self.indexes.value.count(v) else False

        return d_match and g_match and v_match
