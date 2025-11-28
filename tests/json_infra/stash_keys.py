"""Shared StashKey definitions for json_infra tests."""

from typing import Optional

from filelock import FileLock
from pytest import StashKey

desired_forks_key = StashKey[list[str]]()
fixture_lock = StashKey[Optional[FileLock]]()
