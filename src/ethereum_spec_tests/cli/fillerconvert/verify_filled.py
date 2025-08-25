"""Verify refilled test vs original generated test."""

import re
from pathlib import Path

from pydantic import BaseModel, RootModel


# Define only relevant data we need to read from the files
class Indexes(BaseModel):
    """Post Section Indexes."""

    data: int
    gas: int
    value: int


class PostRecord(BaseModel):
    """Post results record."""

    hash: str
    indexes: Indexes


class StateTest(BaseModel):
    """StateTest in filled file."""

    post: dict[str, list[PostRecord]]


class FilledStateTest(RootModel[dict[str, StateTest]]):
    """State Test Wrapper."""


def verify_refilled(refilled: Path, original: Path) -> int:
    """
    Verify post hash of the refilled test against original:
    Regex the original d,g,v from the refilled test name.
    Find the post record for this d,g,v and the fork of refilled test.
    Compare the post hash.
    """
    verified_vectors = 0
    json_str = refilled.read_text(encoding="utf-8")
    refilled_test_wrapper = FilledStateTest.model_validate_json(json_str)

    json_str = original.read_text(encoding="utf-8")
    original_test_wrapper = FilledStateTest.model_validate_json(json_str)

    # Each original test has only 1 test with many posts for each fork and many txs
    original_test_name, test_original = list(original_test_wrapper.root.items())[0]

    for refilled_test_name, refilled_test in refilled_test_wrapper.root.items():
        # Each refilled test has only 1 post for 1 fork and 1 transaction
        refilled_fork, refilled_result = list(refilled_test.post.items())[0]
        pattern = r"v=(\d+)-g=(\d+)-d=(\d+)"
        match = re.search(pattern, refilled_test_name)
        if match:
            v, g, d = match.groups()
            v, g, d = int(v), int(g), int(d)

            found = False
            original_result = test_original.post[refilled_fork]
            for res in original_result:
                if res.indexes.data == d and res.indexes.gas == g and res.indexes.value == v:
                    print(f"check: {refilled_fork}, d:{d}, g:{g}, v:{v}")
                    if res.hash != refilled_result[0].hash:
                        raise Exception(
                            "\nRefilled test post hash mismatch: \n"
                            f"test_name: {refilled_test_name}\n"
                            f"original_name: {original}\n"
                            f"refilled_hash: {refilled_result[0].hash}\n"
                            f"original_hash: {res.hash} f: {refilled_fork}, d: {d}, g: {g}, v: {v}"
                        )
                    found = True
                    verified_vectors += 1
                    break

            if not found:
                raise Exception(
                    "\nRefilled test not found in original: \n"
                    f"test_name: {refilled_test_name}\n"
                    f"original_name: {original}\n"
                )
        else:
            raise Exception("Could not regex match d.g.v indexes from refilled test name!")

    return verified_vectors
