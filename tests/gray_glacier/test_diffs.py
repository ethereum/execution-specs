import os

from tests.helpers.diff_test_helpers import run_diff_test

expected_diffs_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), "expected_diffs"
)


def test_diffs(tmp_path: str) -> None:
    run_diff_test("gray_glacier", expected_diffs_path, tmp_path)
