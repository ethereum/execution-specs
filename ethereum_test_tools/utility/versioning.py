"""
Utility module with helper functions for versioning.
"""

import re

from git import InvalidGitRepositoryError, Repo  # type: ignore


def get_current_commit_hash_or_tag(repo_path=".", shorten_hash=False):
    """
    Get the latest commit tag or commit hash from the repository.

    If a tag points to the current commit, return the tag name.
    If no tag exists:
        - If shorten_hash is True, return the first 8 characters of the commit hash.
        - Otherwise, return the full commit hash.
    """
    try:
        repo = Repo(repo_path)
        # Try to get the current tag that points to the current commit
        current_commit = repo.head.commit
        current_tag = next((tag for tag in repo.tags if tag.commit == current_commit), None)
        if current_tag:
            return current_tag.name
        else:
            commit_hash = current_commit.hexsha
            return commit_hash[:8] if shorten_hash else commit_hash
    except InvalidGitRepositoryError:
        # Handle the case where the repository is not a valid Git repository
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
