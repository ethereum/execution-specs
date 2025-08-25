"""Base class to parse test cases written in static formats."""

import re
from abc import abstractmethod
from typing import Any, Callable, ClassVar, Dict, List, Tuple, Type, Union

from pydantic import (
    BaseModel,
    TypeAdapter,
    ValidatorFunctionWrapHandler,
    model_validator,
)

from ethereum_test_base_types import Bytes


class BaseStaticTest(BaseModel):
    """Represents a base class that reads cases from static files."""

    formats: ClassVar[List[Type["BaseStaticTest"]]] = []
    formats_type_adapter: ClassVar[TypeAdapter]

    format_name: ClassVar[str] = ""

    @classmethod
    def __pydantic_init_subclass__(cls, **kwargs):
        """
        Register all subclasses of BaseStaticTest with a static test format name set
        as possible static test format.
        """
        if cls.format_name:
            # Register the new fixture format
            BaseStaticTest.formats.append(cls)
            if len(BaseStaticTest.formats) > 1:
                BaseStaticTest.formats_type_adapter = TypeAdapter(
                    Union[tuple(BaseStaticTest.formats)],
                )
            else:
                BaseStaticTest.formats_type_adapter = TypeAdapter(cls)

    @model_validator(mode="wrap")
    @classmethod
    def _parse_into_subclass(
        cls, v: Any, handler: ValidatorFunctionWrapHandler
    ) -> "BaseStaticTest":
        """Parse the static test into the correct subclass."""
        if cls is BaseStaticTest:
            return BaseStaticTest.formats_type_adapter.validate_python(v)
        return handler(v)

    @abstractmethod
    def fill_function(self) -> Callable:
        """
        Return the test function that can be used to fill the test.

        This method should be implemented by the subclasses.

        The function returned can be optionally decorated with the `@pytest.mark.parametrize`
        decorator to parametrize the test with the number of sub test cases.

        Example:
        ```
        @pytest.mark.parametrize("n", [1])
        @pytest.mark.parametrize("m", [1, 2])
        @pytest.mark.valid_from("Homestead")
        def test_state_filler(
            state_test: StateTestFiller,
            fork: Fork,
            pre: Alloc,
            n: int,
            m: int,
        ):
            \"\"\"Generate a test from a static state filler.\"\"\"
            assert n == 1
            assert m in [1, 2]
            env = Environment(**self.env.model_dump())
            sender = pre.fund_eoa()
            tx = Transaction(
                ty=0x0,
                nonce=0,
                to=Address(0x1000),
                gas_limit=500000,
                protected=False if fork in [Frontier, Homestead] else True,
                data="",
                sender=sender,
            )
            state_test(env=env, pre=pre, post={}, tx=tx)

        return test_state_filler
        ```

        To aid the generation of the test, the function can be defined and then the decorator be
        applied after defining the function:

        ```
        def test_state_filler(
            state_test: StateTestFiller,
            fork: Fork,
            pre: Alloc,
            n: int,
            m: int,
        ):
            ...
        test_state_filler = pytest.mark.parametrize("n", [1])(test_state_filler)
        test_state_filler = pytest.mark.parametrize("m", [1, 2])(test_state_filler)
        if self.valid_from:
            test_state_filler = pytest.mark.valid_from(self.valid_from)(test_state_filler)
        if self.valid_until:
            test_state_filler = pytest.mark.valid_until(self.valid_until)(test_state_filler)
        return test_state_filler
        ```

        The function can contain the following parameters on top of the spec type parameter
        (`state_test` in the example above):
        - `fork`: The fork for which the test is currently being filled.
        - `pre`: The pre-state of the test.

        """
        raise NotImplementedError

    @staticmethod
    def remove_comments(data: Dict) -> Dict:
        """Remove comments from a dictionary."""
        result = {}
        for k, v in data.items():
            if isinstance(k, str) and k.startswith("//"):
                continue
            if isinstance(v, dict):
                v = BaseStaticTest.remove_comments(v)
            elif isinstance(v, list):
                v = [BaseStaticTest.remove_comments(i) if isinstance(i, dict) else i for i in v]
            result[k] = v
        return result

    @model_validator(mode="before")
    @classmethod
    def remove_comments_from_model(cls, data: Any) -> Any:
        """Remove comments from the static file loaded, if any."""
        if isinstance(data, dict):
            return BaseStaticTest.remove_comments(data)
        return data


def remove_comments(v: str) -> str:
    """
    Split by line and then remove the comments (starting with #) at the end of each line if
    any.
    """
    return "\n".join([line.split("#")[0].strip() for line in v.splitlines()])


label_matcher = re.compile(r"^:label\s+(\S+)\s*", re.MULTILINE)
raw_matcher = re.compile(r":raw\s+(.*)", re.MULTILINE)


def labeled_bytes_from_string(v: str) -> Tuple[str | None, Bytes]:
    """Parse `:label` and `:raw` from a string."""
    v = remove_comments(v)

    label: str | None = None
    if m := label_matcher.search(v):
        label = m.group(1)
        v = label_matcher.sub("", v)

    m = raw_matcher.match(v.replace("\n", " "))
    if not m:
        raise Exception(f"Unable to parse container from string: {v}")
    strip_string = m.group(1).strip()
    return label, Bytes(strip_string)
