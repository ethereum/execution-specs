"""
Utility module with helper functions for versioning.
"""

import re

from git import InvalidGitRepositoryError, Repo  # type: ignore


def get_current_commit_hash_or_tag(repo_path="."):
    """
    Get the latest commit hash or tag from the clone where doc is being built.
    """
    try:
        repo = Repo(repo_path)
        # Try to get the current tag that points to the current commit
        current_tag = next((tag for tag in repo.tags if tag.commit == repo.head.commit), None)
        # Return the commit hash if no such tag exits
        return current_tag.name if current_tag else repo.head.commit.hexsha
    except InvalidGitRepositoryError:
        # This hack is necessary for our framework tests. We use the pytester/tempdir fixtures
        # to execute pytest within a pytest session (for top-level tests of our pytest plugins).
        # The pytester fixture executes these tests in a temporary directory, which is not a git
        # repository; this is a workaround to stop these tests failing.
        #
        # Tried monkeypatching the pytest plugin tests, but it didn't play well with pytester.
        return "Not a git repository; this should only be seen in framework tests."


def generate_github_url(file_path, branch_or_commit_or_tag="main", line_number=""):
    """
    Generate a permalink to a source file in Github.
    """
    base_url = "https://github.com"
    username = "ethereum"
    repository = "execution-spec-tests"
    if line_number:
        line_number = f"#L{line_number}"
    release_tag_regex = r"^v[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}(a[0-9]+|b[0-9]+|rc[0-9]+)?$"
    tree_or_blob = "tree" if re.match(release_tag_regex, branch_or_commit_or_tag) else "blob"
    return (
        f"{base_url}/{username}/{repository}/{tree_or_blob}/"
        f"{branch_or_commit_or_tag}/{file_path}{line_number}"
    )
