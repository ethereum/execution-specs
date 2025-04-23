"""Ethereum/tests state test Filler structure."""

from typing import Dict, List, Union

from pydantic import BaseModel, Field, model_validator

from ethereum_test_forks import Fork
from ethereum_test_types import Alloc, Environment, Transaction

from .account import AccountInFiller
from .common import AddressInFiller
from .environment import EnvironmentInStateTestFiller
from .expect_section import ExpectSectionInStateTestFiller
from .general_transaction import GeneralTransactionInFiller


class Info(BaseModel):
    """Class that represents an info filler."""

    comment: str | None = Field(None)
    pytest_marks: List[str] = Field(default_factory=list)


class StateTestInFiller(BaseModel):
    """A single test in state test filler."""

    info: Info | None = Field(None, alias="_info")
    env: EnvironmentInStateTestFiller
    pre: Dict[AddressInFiller, AccountInFiller]
    transaction: GeneralTransactionInFiller
    expect: List[ExpectSectionInStateTestFiller]
    solidity: str | None = Field(None)

    class Config:
        """Model Config."""

        extra = "forbid"

    @model_validator(mode="after")
    def match_labels(self) -> "StateTestInFiller":
        """Replace labels in expect section with corresponding tx.d indexes."""

        def parse_string_indexes(indexes: str) -> List[int]:
            """Parse index that are string in to list of int."""
            if ":label" in indexes:
                # Parse labels in data
                indexes = indexes.replace(":label ", "")
                tx_matches: List[int] = []
                for idx, d in enumerate(self.transaction.data):
                    if indexes == d.data.code_label:
                        tx_matches.append(idx)
                return tx_matches
            else:
                # Prase ranges in data
                start, end = map(int, indexes.lstrip().split("-"))
                return list(range(start, end + 1))

        def parse_indexes(
            indexes: Union[int, str, list[Union[int, str]], list[str], list[int]],
            do_hint: bool = False,
        ) -> List[int] | int:
            """Prase indexes and replace all ranges and labels into tx indexes."""
            result: List[int] | int = []

            if do_hint:
                print("Before: " + str(indexes))

            if isinstance(indexes, int):
                result = indexes
            if isinstance(indexes, str):
                result = parse_string_indexes(indexes)
            if isinstance(indexes, list):
                result = []
                for element in indexes:
                    parsed = parse_indexes(element)
                    if isinstance(parsed, int):
                        result.append(parsed)
                    else:
                        result.extend(parsed)
                result = list(set(result))

            if do_hint:
                print("After: " + str(result))
            return result

        for expect_section in self.expect:
            expect_section.indexes.data = parse_indexes(expect_section.indexes.data)
            expect_section.indexes.gas = parse_indexes(expect_section.indexes.gas)
            expect_section.indexes.value = parse_indexes(expect_section.indexes.value)

        return self


def serialize_fork(value: Fork):
    """Pydantic serialize FORK."""
    return value.name()


class StateTestVector(BaseModel):
    """A data from .json test filler that is required for a state test vector."""

    id: str
    env: Environment
    pre: Alloc
    tx: Transaction
    tx_exception: str | None
    post: Alloc
    fork: Fork

    class Config:
        """Serialize config."""

        json_encoders = {
            Fork: serialize_fork,
        }
