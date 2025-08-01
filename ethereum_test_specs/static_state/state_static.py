"""Ethereum General State Test filler static test spec parser."""

from typing import Callable, ClassVar, List, Self, Set, Union

import pytest
from _pytest.mark.structures import ParameterSet
from pydantic import BaseModel, Field, model_validator

from ethereum_test_forks import Fork
from ethereum_test_types import Alloc

from ..base_static import BaseStaticTest
from ..state import StateTestFiller
from .account import PreInFiller
from .common import Tag
from .environment import EnvironmentInStateTestFiller
from .expect_section import ExpectSectionInStateTestFiller
from .general_transaction import GeneralTransactionInFiller


class Info(BaseModel):
    """Class that represents an info filler."""

    comment: str | None = Field(None)
    pytest_marks: List[str] = Field(default_factory=list)


class StateStaticTest(BaseStaticTest):
    """General State Test static filler from ethereum/tests."""

    test_name: str = ""
    format_name: ClassVar[str] = "state_test"

    info: Info | None = Field(None, alias="_info")
    env: EnvironmentInStateTestFiller
    pre: PreInFiller
    transaction: GeneralTransactionInFiller
    expect: List[ExpectSectionInStateTestFiller]

    class Config:
        """Model Config."""

        extra = "forbid"

    def model_post_init(self, context):
        """Initialize StateStaticTest."""
        super().model_post_init(context)

    @model_validator(mode="after")
    def match_labels(self) -> Self:
        """Replace labels in expect section with corresponding tx.d indexes."""

        def parse_string_indexes(indexes: str) -> List[int]:
            """Parse index that are string in to list of int."""
            if ":label" in indexes:
                # Parse labels in data
                indexes = indexes.replace(":label ", "")
                tx_matches: List[int] = []
                for idx in self.transaction.data:
                    if indexes == idx.label:
                        tx_matches.append(idx.index)
                return tx_matches
            else:
                # Parse ranges in data
                start, end = map(int, indexes.lstrip().split("-"))
                return list(range(start, end + 1))

        def parse_indexes(
            indexes: Union[int, str, list[Union[int, str]], list[str], list[int]],
            do_hint: bool = False,
        ) -> List[int] | int:
            """Parse indexes and replace all ranges and labels into tx indexes."""
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

    def fill_function(self) -> Callable:
        """Return a StateTest spec from a static file."""
        # Check if this test uses tags
        has_tags = False
        tx_tag_dependencies = self.transaction.tag_dependencies()
        if tx_tag_dependencies:
            has_tags = True
        else:
            # Check expect sections for tags
            for expect in self.expect:
                result_tag_dependencies = expect.result.tag_dependencies()
                if result_tag_dependencies:
                    has_tags = True
                    break

        fully_tagged = True
        for address in self.pre.root:
            if not isinstance(address, Tag):
                fully_tagged = False
                break

        d_g_v_parameters: List[ParameterSet] = []
        for d in self.transaction.data:
            for g in range(len(self.transaction.gas_limit)):
                for v in range(len(self.transaction.value)):
                    exception_test = False
                    for expect in self.expect:
                        if expect.has_index(d.index, g, v) and expect.expect_exception is not None:
                            exception_test = True
                    # TODO: This does not take into account exceptions that only happen on
                    #       specific forks, but this requires a covariant parametrize
                    marks = [pytest.mark.exception_test] if exception_test else []
                    id_label = ""
                    if len(self.transaction.data) > 1 or d.label is not None:
                        if d.label is not None:
                            id_label = f"{d}"
                        else:
                            id_label = f"d{d}"
                    if len(self.transaction.gas_limit) > 1:
                        id_label += f"-g{g}"
                    if len(self.transaction.value) > 1:
                        id_label += f"-v{v}"
                    d_g_v_parameters.append(pytest.param(d.index, g, v, marks=marks, id=id_label))

        @pytest.mark.valid_at(*self.get_valid_at_forks())
        @pytest.mark.parametrize("d,g,v", d_g_v_parameters)
        def test_state_vectors(
            state_test: StateTestFiller,
            pre: Alloc,
            fork: Fork,
            d: int,
            g: int,
            v: int,
        ):
            for expect in self.expect:
                if expect.has_index(d, g, v):
                    if fork in expect.network:
                        tx_tag_dependencies = self.transaction.tag_dependencies()
                        result_tag_dependencies = expect.result.tag_dependencies()
                        all_dependencies = {**tx_tag_dependencies, **result_tag_dependencies}
                        tags = self.pre.setup(pre, all_dependencies)
                        env = self.env.get_environment(tags)
                        exception = (
                            None
                            if expect.expect_exception is None
                            else expect.expect_exception[fork]
                        )
                        tx = self.transaction.get_transaction(tags, d, g, v, exception)
                        post = expect.result.resolve(tags)
                        return state_test(
                            env=env,
                            pre=pre,
                            post=post,
                            tx=tx,
                        )
            pytest.fail(f"Expectation not found for d={d}, g={g}, v={v}, fork={fork}")

        if self.info and self.info.pytest_marks:
            for mark in self.info.pytest_marks:
                apply_mark = getattr(pytest.mark, mark)
                test_state_vectors = apply_mark(test_state_vectors)

        if has_tags:
            test_state_vectors = pytest.mark.tagged(test_state_vectors)
            if fully_tagged:
                test_state_vectors = pytest.mark.fully_tagged(test_state_vectors)
        else:
            test_state_vectors = pytest.mark.untagged(test_state_vectors)

        return test_state_vectors

    def get_valid_at_forks(self) -> List[str]:
        """Return list of forks that are valid for this test."""
        fork_set: Set[Fork] = set()
        for expect in self.expect:
            fork_set.update(expect.network)
        return sorted([str(f) for f in fork_set])
