"""
EIP-1153 Tests
"""

from enum import Enum, unique

import pytest

from ethereum_test_tools import Opcodes as Op


class PytestParameterEnum(Enum):
    """
    Helper class for defining Pytest parameters used in test cases.

    This class helps define enum `value`s as `pytest.param` objects that can be
    passed to `pytest.mark.parametrize()`. It defines an additional `params`
    property to access the `pytest.param` value. And an `as_list()` method to
    return a list of all enum `pytest.param` values, for example,

    ```python
    @pytest.mark.parametrize("test_value", TStorageCallContextTestCases.as_list())
    def test_function(test_value):
        pass
    ```

    Classes which derive from this class must define a:

    1. A dictionary that contains:
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

        Other values may be present in the dictionary.

    2. An object `test_case` that contains the test case parameters as
        used by the fixture and test functions. This can be a single value
        or a tuple of values.

    and pass these values to the superclass constructor. Note, the `test_case`
    can be defined directly in the enum value or constructed in the class's
    `__init__()` method.

    The test case ID is set as the enum name converted to lowercase.
    """

    def __init__(self, value, test_case):
        if "pytest_marks" in value:
            marks = {"marks": value["pytest_marks"]}
        else:
            marks = {}
        self.description = value["description"]
        if isinstance(test_case, list) or isinstance(test_case, tuple):
            self._value_ = pytest.param(*test_case, id=self.name.lower(), **marks)
        else:
            self._value_ = pytest.param(test_case, id=self.name.lower(), **marks)

    @property
    def params(self):
        """
        Return the `pytest.param` value for this test case.
        """
        return self._value_

    @classmethod
    def as_list(cls):
        """
        Return a list of the enum values.
        """
        return [test_case.params for test_case in cls]


@unique
class CreateOpcodeParams(PytestParameterEnum):
    """
    Helper enum class to parametrize tests with different contract creation
    opcodes: CREATE and CREATE2.
    """

    CREATE = {"opcode": Op.CREATE, "description": "Test CREATE opcode."}
    CREATE2 = {"opcode": Op.CREATE2, "description": "Test CREATE2 opcode."}

    def __init__(self, test_case_params):
        test_case = test_case_params["opcode"]
        super().__init__(test_case_params, test_case)
