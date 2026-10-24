# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
#     "requests",
# ]
# ///
"""Select and assign a single reviewer for a GitHub PR."""

import argparse
import json
import os
import random
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
import yaml

TEAM_FILE = ".github/team.yml"

WEIGHTS_STANDARD = {
    "workload": 0.25,
    "familiarity_most": 0.20,
    "familiarity_least": 0.15,
    "recency": 0.20,
    "complexity_match": 0.10,
}

WEIGHTS_TRIVIAL = {
    "workload": 0.25,
    "familiarity_most": 0.15,
    "familiarity_least": 0.20,
    "recency": 0.20,
    "complexity_match": 0.10,
}


def warn(msg):
    """Print a warning to stderr."""
    print(f"warning: {msg}", file=sys.stderr)


def fatal(msg):
    """Print an error to stderr and exit."""
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def gh(*args):
    """Run a gh CLI command and return stdout."""
    result = subprocess.run(
        ["gh", *args],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def gh_json(*args):
    """Run a gh CLI command and parse stdout as JSON."""
    raw = gh(*args)
    if raw is None:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def load_team(repo_root):
    """Load the team roster from team.yml."""
    path = Path(repo_root) / TEAM_FILE
    if not path.exists():
        fatal(f"team file not found: {path}")
    with open(path) as team_file:
        data = yaml.safe_load(team_file)
    return data.get("reviewers", [])


def fetch_ooo_emails():
    """Return emails of team members currently OOO."""
    url = os.environ.get("STEEL_OOO_URL")
    key = os.environ.get("STEEL_OOO_KEY")
    if not url or not key:
        warn("STEEL_OOO_URL or STEEL_OOO_KEY not set, skipping OOO check")
        return set()
    try:
        resp = requests.get(url, params={"key": key}, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        return {
            event["creator"]
            for event in data.get("ooo", [])
            if event.get("creator")
        }
    except Exception as e:
        warn(f"OOO endpoint failed: {e}")
        return set()


def fetch_pr_info(repo, pr_number):
    """Fetch PR metadata via gh CLI."""
    data = gh_json(
        "pr",
        "view",
        str(pr_number),
        "-R",
        repo,
        "--json",
        "author,additions,deletions,commits,headRefName",
    )
    if data is None:
        fatal(f"could not fetch PR #{pr_number}")
    return data


def fetch_pr_files(repo, pr_number):
    """Return list of file paths changed in a PR."""
    raw = gh(
        "pr",
        "diff",
        str(pr_number),
        "-R",
        repo,
        "--name-only",
    )
    if raw is None:
        return []
    return [line for line in raw.splitlines() if line.strip()]


def fetch_branch_contributors(pr_info):
    """Extract unique commit author logins from PR commits."""
    contributors = set()
    for commit in pr_info.get("commits", []):
        authors = commit.get("authors", [])
        for author in authors:
            login = author.get("login")
            if login:
                contributors.add(login.lower())
    return contributors


def fetch_recent_contributors(repo, pr_number):
    """Get authors who pushed since last review."""
    reviews = gh_json(
        "api",
        f"repos/{repo}/pulls/{pr_number}/reviews",
        "--jq",
        ".",
    )
    if not reviews:
        return set(), None

    last_request_time = None
    for review in reversed(reviews):
        submitted = review.get("submitted_at")
        if submitted:
            last_request_time = datetime.fromisoformat(
                submitted.replace("Z", "+00:00")
            )
            break

    if last_request_time is None:
        return fetch_branch_contributors(fetch_pr_info(repo, pr_number)), None

    commits = gh_json(
        "api",
        f"repos/{repo}/pulls/{pr_number}/commits",
        "--jq",
        ".",
    )
    recent = set()
    if commits:
        for commit in commits:
            date_str = (
                commit.get("commit", {}).get("author", {}).get("date", "")
            )
            if not date_str:
                continue
            commit_time = datetime.fromisoformat(
                date_str.replace("Z", "+00:00")
            )
            if commit_time > last_request_time:
                login = (commit.get("author", {}) or {}).get("login")
                if login:
                    recent.add(login.lower())
    return recent, last_request_time


def fetch_review_data(repo, candidates):
    """Fetch workload, last review dates, and review counts via GraphQL."""
    owner, name = repo.split("/")
    search_queries = []
    for i, candidate in enumerate(sorted(candidates)):
        alias = f"u{i}"
        search_queries.append(
            f'{alias}: search(query: "repo:{repo} '
            f'is:pr is:open review-requested:{candidate}", '
            f"type: ISSUE, first: 0) {{ issueCount }}"
        )
    searches = "\n    ".join(search_queries)
    query = f"""{{
    repository(owner: "{owner}", name: "{name}") {{
        pullRequests(
            last: 50, states: [OPEN, CLOSED, MERGED]
        ) {{
            nodes {{
                reviews(last: 50) {{
                    nodes {{
                        author {{ login }}
                        submittedAt
                    }}
                }}
            }}
        }}
    }}
    {searches}
}}"""
    data = gh_json(
        "api",
        "graphql",
        "-f",
        f"query={query}",
    )
    if not data or "data" not in data:
        warn("GraphQL review query failed")
        return (
            dict.fromkeys(candidates, 0),
            dict.fromkeys(candidates, None),
            dict.fromkeys(candidates, 0),
        )

    gql = data["data"]
    workload = {}
    for i, candidate in enumerate(sorted(candidates)):
        alias = f"u{i}"
        node = gql.get(alias, {})
        workload[candidate] = node.get("issueCount", 0)

    last_review = dict.fromkeys(candidates, None)
    review_counts = dict.fromkeys(candidates, 0)
    prs = gql.get("repository", {}).get("pullRequests", {}).get("nodes", [])
    for pr in prs:
        seen = set()
        for review in pr.get("reviews", {}).get("nodes", []):
            author = (review.get("author") or {}).get("login", "").lower()
            submitted = review.get("submittedAt")
            if not author or not submitted:
                continue
            ts = datetime.fromisoformat(submitted.replace("Z", "+00:00"))
            if author in last_review:
                prev = last_review[author]
                if prev is None or ts > prev:
                    last_review[author] = ts
            if author in review_counts and author not in seen:
                review_counts[author] += 1
                seen.add(author)

    return workload, last_review, review_counts


def fetch_file_familiarity(repo, files):
    """Count per-author commits in directories touched by the PR."""
    owner, name = repo.split("/")
    dirs_seen = set()
    unique_dirs = []
    for filepath in files:
        dir_path = str(Path(filepath).parent)
        if dir_path not in dirs_seen:
            dirs_seen.add(dir_path)
            unique_dirs.append(dir_path)

    unique_dirs = unique_dirs[:10]

    history_queries = []
    for i, directory in enumerate(unique_dirs):
        alias = f"d{i}"
        history_queries.append(
            f"{alias}: history("
            f'first: 30, path: "{directory}"'
            f") {{ nodes {{ author {{ user {{ login }} }} }} }}"
        )
    histories = "\n          ".join(history_queries)
    if not histories:
        return {}

    query = f"""{{
    repository(owner: "{owner}", name: "{name}") {{
        defaultBranchRef {{
            target {{
                ... on Commit {{
                    {histories}
                }}
            }}
        }}
    }}
}}"""
    data = gh_json(
        "api",
        "graphql",
        "-f",
        f"query={query}",
    )
    if not data or "data" not in data:
        warn("GraphQL familiarity query failed")
        return {}

    commit_node = (
        data["data"]
        .get("repository", {})
        .get("defaultBranchRef", {})
        .get("target", {})
    )
    counts = {}
    for i in range(len(unique_dirs)):
        alias = f"d{i}"
        nodes = commit_node.get(alias, {}).get("nodes", [])
        for node in nodes:
            login = ((node.get("author") or {}).get("user") or {}).get(
                "login", ""
            )
            if login:
                key = login.lower()
                counts[key] = counts.get(key, 0) + 1
    return counts


def compute_complexity(additions, deletions, num_files):
    """Return a 0.0-1.0 complexity score for a PR."""
    churn = additions + deletions
    if churn > 500 or num_files > 20:
        return 1.0
    if churn > 150 or num_files > 8:
        return 0.6
    if churn > 50 or num_files > 3:
        return 0.3
    return 0.1


def normalise(scores):
    """Normalize scores using min-max between 0 and 1."""
    if not scores:
        return {}
    vals = list(scores.values())
    lo, hi = min(vals), max(vals)
    if lo == hi:
        return dict.fromkeys(scores, 0.5)
    return {k: (v - lo) / (hi - lo) for k, v in scores.items()}


def select_reviewer(
    repo,
    pr_number,
    repo_root,
    mode,
    verbose=False,
):
    """Score candidates and return the best reviewer."""
    team = load_team(repo_root)
    email_to_user = {
        teammate["email"].lower(): teammate["username"].lower()
        for teammate in team
    }
    all_usernames = {teammate["username"].lower() for teammate in team}

    pr_info = fetch_pr_info(repo, pr_number)
    pr_author = pr_info["author"]["login"].lower()
    pr_files = fetch_pr_files(repo, pr_number)
    additions = pr_info.get("additions", 0)
    deletions = pr_info.get("deletions", 0)
    complexity = compute_complexity(additions, deletions, len(pr_files))

    candidates = set(all_usernames)
    candidates.discard(pr_author)

    if mode == "initial":
        branch_contribs = fetch_branch_contributors(pr_info)
        candidates -= branch_contribs
    else:
        recent, _ = fetch_recent_contributors(repo, pr_number)
        candidates -= recent
        candidates.discard(pr_author)

    ooo_emails = fetch_ooo_emails()
    ooo_users = {
        email_to_user[e.lower()]
        for e in ooo_emails
        if e.lower() in email_to_user
    }
    candidates -= ooo_users

    if not candidates:
        fatal("no eligible candidates remain after exclusions")
    if len(candidates) == 1:
        return candidates.pop()

    weights = WEIGHTS_TRIVIAL if complexity <= 0.1 else WEIGHTS_STANDARD

    workload, last_review, review_counts = fetch_review_data(repo, candidates)

    raw_workload = {
        candidate: -(workload.get(candidate, 0)) for candidate in candidates
    }
    n_workload = normalise(raw_workload)

    familiarity = fetch_file_familiarity(repo, pr_files)
    raw_fam_most = {
        candidate: familiarity.get(candidate, 0) for candidate in candidates
    }
    raw_fam_least = {
        candidate: -familiarity.get(candidate, 0) for candidate in candidates
    }
    n_fam_most = normalise(raw_fam_most)
    n_fam_least = normalise(raw_fam_least)

    now = datetime.now(timezone.utc)
    raw_recency = {}
    for candidate in candidates:
        last = last_review.get(candidate)
        if last is None:
            raw_recency[candidate] = 365
        else:
            raw_recency[candidate] = (now - last).days
    n_recency = normalise(raw_recency)

    max_reviews = max(review_counts.values()) or 1
    raw_complexity = {}
    for candidate in candidates:
        experience = review_counts.get(candidate, 0) / max_reviews
        raw_complexity[candidate] = 1.0 - abs(experience - complexity)
    n_complexity = normalise(raw_complexity)

    final_scores = {}
    for candidate in candidates:
        score = (
            weights["workload"] * n_workload.get(candidate, 0.5)
            + weights["familiarity_most"] * n_fam_most.get(candidate, 0.5)
            + weights["familiarity_least"] * n_fam_least.get(candidate, 0.5)
            + weights["recency"] * n_recency.get(candidate, 0.5)
            + weights["complexity_match"] * n_complexity.get(candidate, 0.5)
        )
        final_scores[candidate] = score

    if verbose:
        ranked = sorted(
            final_scores.items(),
            key=lambda candidate_and_score: candidate_and_score[1],
            reverse=True,
        )
        warn("--- scoring breakdown ---")
        warn(
            f"{'candidate':<20} {'work':>5} "
            f"{'fam+':>5} {'fam-':>5} "
            f"{'recn':>5} {'cmpl':>5} {'TOTAL':>7}"
        )
        for name, total in ranked:
            warn(
                f"{name:<20} "
                f"{n_workload.get(name, 0):>5.2f} "
                f"{n_fam_most.get(name, 0):>5.2f} "
                f"{n_fam_least.get(name, 0):>5.2f} "
                f"{n_recency.get(name, 0):>5.2f} "
                f"{n_complexity.get(name, 0):>5.2f} "
                f"{total:>7.4f}"
            )
        warn("-------------------------")

    max_score = max(final_scores.values())
    tied = [
        candidate
        for candidate, score in final_scores.items()
        if abs(score - max_score) < 1e-9
    ]
    winner = random.choice(tied)

    original_case = {
        teammate["username"].lower(): teammate["username"] for teammate in team
    }
    return original_case.get(winner, winner)


def main():
    """Parse arguments and run reviewer assignment."""
    parser = argparse.ArgumentParser(
        description="Assign a reviewer to a GitHub PR"
    )
    parser.add_argument(
        "--repo",
        required=True,
        help="owner/repo (e.g. ethereum/execution-specs)",
    )
    parser.add_argument(
        "--pr",
        required=True,
        type=int,
        help="PR number",
    )
    parser.add_argument(
        "--mode",
        choices=["initial", "rereview"],
        default="initial",
        help="initial for new PRs, rereview after fixes",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="path to repo root (for team.yml)",
    )
    parser.add_argument(
        "--assign",
        action="store_true",
        help="assign the reviewer via gh pr edit",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="print scoring breakdown to stderr",
    )
    args = parser.parse_args()

    reviewer = select_reviewer(
        args.repo,
        args.pr,
        args.repo_root,
        args.mode,
        verbose=args.verbose,
    )
    print(reviewer)

    if args.assign:
        gh(
            "pr",
            "edit",
            str(args.pr),
            "-R",
            args.repo,
            "--add-reviewer",
            reviewer,
        )


if __name__ == "__main__":
    main()
