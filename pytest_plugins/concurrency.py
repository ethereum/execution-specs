"""
Pytest plugin to create a temporary folder for the session where
multi-process tests can store data that is shared between processes.

The provided `session_temp_folder` fixture is used, for example, by `consume`
when running hive simulators to ensure that only one `test_suite` is created
(used to create tests on the hive simulator) when they are being created using
multiple workers with pytest-xdist.
"""

import os
import shutil
from pathlib import Path
from tempfile import gettempdir as get_temp_dir  # noqa: SC200
from typing import Generator

import pytest
from filelock import FileLock


@pytest.fixture(scope="session")
def session_temp_folder_name(testrun_uid: str) -> str:  # noqa: SC200
    """
    Define the name of the temporary folder that will be shared among all the
    xdist workers to coordinate the tests.

    "testrun_uid" is a fixture provided by the xdist plugin, and is unique for each test run,
    so it is used to create the unique folder name.
    """
    return f"pytest-{testrun_uid}"  # noqa: SC200


@pytest.fixture(scope="session")
def session_temp_folder(
    session_temp_folder_name: str,
) -> Generator[Path, None, None]:
    """
    Create a global temporary folder that will be shared among all the
    xdist workers to coordinate the tests.

    We also create a file to keep track of how many workers are still using the folder, so we can
    delete it when the last worker is done.
    """
    session_temp_folder = Path(get_temp_dir()) / session_temp_folder_name
    session_temp_folder.mkdir(exist_ok=True)

    folder_users_file_name = "folder_users"
    folder_users_file = session_temp_folder / folder_users_file_name
    folder_users_lock_file = session_temp_folder / f"{folder_users_file_name}.lock"

    with FileLock(folder_users_lock_file):
        if folder_users_file.exists():
            with folder_users_file.open("r") as f:
                folder_users = int(f.read())
        else:
            folder_users = 0
        folder_users += 1
        with folder_users_file.open("w") as f:
            f.write(str(folder_users))

    yield session_temp_folder

    with FileLock(folder_users_lock_file):
        with folder_users_file.open("r") as f:
            folder_users = int(f.read())
        folder_users -= 1
        if folder_users == 0:
            shutil.rmtree(session_temp_folder)
        else:
            with folder_users_file.open("w") as f:
                f.write(str(folder_users))


@pytest.fixture(scope="session")
def worker_count() -> int:
    """
    Get the number of workers for the test.
    """
    worker_count_env = os.environ.get("PYTEST_XDIST_WORKER_COUNT", "1")
    return max(int(worker_count_env), 1)
