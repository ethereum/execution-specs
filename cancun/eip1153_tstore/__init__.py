"""
EIP-1153 Tests
"""

from enum import Enum, unique
from pprint import pprint
from typing import List

import pytest

from ethereum_test_tools import Opcodes as Op


class PytestParameterEnum(Enum):
    """
    Helper class for defining Pytest parameters used in test cases.

    This class helps define enum `value`s as `pytest.param` objects that then can
    be used to create a parametrize decorator that can be applied to tests,
    for example,

    ```python
    @TStorageCallContextTestCases.parametrize()
    def test_function(test_value):
        pass
    ```

    Classes which derive from this class must define each test case as a different enum
    field with a dictionary as value.

    The dictionary must contain:
        i. A `description` key with a string value describing the test case.
        ii. (Optional) A `pytest_marks` key with a single mark or list of pytest
            marks to apply to the test case. For example,

            ```
            pytest_marks=pytest.mark.xfail
            ```
            or

            ```
            pytest_marks=[pytest.mark.xfail, pytest.mark.skipif]
            ```
        iii. (Optional) An `id` key with the name of the test.

        The rest of the keys in the dictionary are the parameters of the test case.

    The test case ID is set as the enum name converted to lowercase.
    """

    def __init__(self, value):
        assert isinstance(value, dict)
        assert "description" in value
        self._value_ = value

    def param(self, names: List[str]):
        """
        Return the `pytest.param` value for this test case.
        """
        value = self._value_
        if "pytest_marks" in value:
            marks = {"marks": value["pytest_marks"]}
        else:
            marks = {}
        if "pytest_id" in value:
            id = value["pytest_id"]
        else:
            id = self.name.lower()
        return pytest.param(*[value[name] for name in names], id=id, **marks)

    @classmethod
    def special_keywords(cls) -> List[str]:
        """
        Return the special dictionary keywords that are not test parameters.
        """
        return ["description", "pytest_marks", "pytest_id"]

    def names(self) -> List[str]:
        """
        Return the names of all the parameters included in the enum value dict.
        """
        return sorted([k for k in self._value_.keys() if k not in self.special_keywords()])

    @property
    def description(self):
        """
        Returns the description of this test case.
        """
        return self._value_["description"]

    @classmethod
    def parametrize(cls):
        """
        Returns the decorator to parametrize a test with this enum.
        """
        names = None
        for test_case_names in [test_case.names() for test_case in cls]:
            if names is None:
                names = test_case_names
            else:
                if set(names) != set(test_case_names):
                    pprint(names)
                    pprint(test_case_names)
                assert set(names) == set(
                    test_case_names
                ), "All test cases must have the same parameter names."
        assert names is not None, "Enum must have at least one test case."

        return pytest.mark.parametrize(names, [test_case.param(names) for test_case in cls])


@unique
class CreateOpcodeParams(PytestParameterEnum):
    """
    Helper enum class to parametrize tests with different contract creation
    opcodes: CREATE and CREATE2.
    """

    CREATE = {"opcode": Op.CREATE, "description": "Test CREATE opcode."}
    CREATE2 = {"opcode": Op.CREATE2, "description": "Test CREATE2 opcode."}
