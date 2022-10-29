import os
from tests.helpers.diff_test_helpers import run_diff_test

expected_diffs_path = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "expected_diffs"
)


def test_diffs():
    run_diff_test("muir_glacier", expected_diffs_path)
