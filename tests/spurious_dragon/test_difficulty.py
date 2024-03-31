import pytest

from ..helpers.load_difficulty_tests import DifficultyTestLoader

test_loader = DifficultyTestLoader("EIP158", "spurious_dragon")


@pytest.mark.parametrize("test_file", test_loader.test_files)
def test_difficulty(test_file: str) -> None:
    test_list = test_loader.load_test(test_file)

    for test in test_list:
        inputs = test["inputs"]
        assert test["expected"] == test_loader.calculate_block_difficulty(
            inputs["block_number"],
            inputs["block_timestamp"],
            inputs["parent_timestamp"],
            inputs["parent_difficulty"],
        )
