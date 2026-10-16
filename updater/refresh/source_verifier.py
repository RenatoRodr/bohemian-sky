"""Verify an immutable public package commit before it reaches refresh_core.

The review provider is a trusted, authenticated GitHub adapter supplied by the
installer. Repository files, local receipts, and Git commit messages are never
accepted as evidence of review.
"""
import json
import re
import subprocess
import shutil
from pathlib import Path

from refresh_core import EXPECTED, SOURCE_ONLY, RefreshError, digest, _manifest

REPOSITORY = "RenatoRodr/bohemian-sky"
ORIGIN = "https://github.com/RenatoRodr/bohemian-sky.git"
MANIFEST_NAME = "package-manifest.json"
PACKAGE_ROOTS = ("agents/", "skills/", "updater/")
SHA = re.compile(r"[0-9a-f]{40}\Z")


def git(repo, *args):
    try:
        return subprocess.run(["git", *args], cwd=repo, check=True,
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              timeout=15).stdout
    except (OSError, subprocess.SubprocessError) as exc:
        raise RefreshError(f"Git verification failed: {' '.join(args)}: {exc}") from exc


def github_review(repository, commit):
    """Query authenticated GitHub API; repository content is never review evidence."""
    if shutil.which("gh") is None:
        raise RefreshError("authenticated GitHub CLI unavailable")
    def api(path):
        try:
            completed = subprocess.run(["gh", "api", path], check=True,
                                       capture_output=True, timeout=15)
            return json.loads(completed.stdout)
        except (OSError, subprocess.SubprocessError, ValueError) as exc:
            raise RefreshError(f"GitHub review API failed: {path}: {exc}") from exc
    pulls = api(f"repos/{repository}/commits/{commit}/pulls")
    if not isinstance(pulls, list) or len(pulls) != 1:
        raise RefreshError("reviewed merge provenance missing or ambiguous")
    pr = pulls[0]
    if not isinstance(pr, dict) or not isinstance(pr.get("number"), int):
        raise RefreshError("invalid GitHub pull request evidence")
    detail = api(f"repos/{repository}/pulls/{pr['number']}")
    reviews = api(f"repos/{repository}/pulls/{pr['number']}/reviews?per_page=100")
    if not isinstance(detail, dict) or not isinstance(reviews, list):
        raise RefreshError("invalid GitHub review evidence")
    merged_at = detail.get("merged_at")
    if not isinstance(merged_at, str) or not merged_at or len(reviews) >= 100:
        raise RefreshError("incomplete GitHub review evidence")
    head = detail.get("head")
    head_sha = head.get("sha") if isinstance(head, dict) else None
    base = detail.get("base")
    base_repo = base.get("repo") if isinstance(base, dict) else None
    base_full_name = base_repo.get("full_name") if isinstance(base_repo, dict) else None
    base_ref = base.get("ref") if isinstance(base, dict) else None
    merge_sha = detail.get("merge_commit_sha")
    if not isinstance(head_sha, str) or not SHA.fullmatch(head_sha):
        raise RefreshError("invalid merged pull request head")
    if base_full_name != REPOSITORY or base_ref != "main" or not isinstance(merge_sha, str) or not SHA.fullmatch(merge_sha):
        raise RefreshError("merged pull request base or merge commit differs")
    latest = {}
    for row in reviews:
        if not isinstance(row, dict) or not isinstance(row.get("user"), dict):
            raise RefreshError("ambiguous GitHub review evidence")
        login, state, submitted, review_commit = (row["user"].get("login"), row.get("state"),
                                    row.get("submitted_at"), row.get("commit_id"))
        if not isinstance(login, str) or not login or state not in ("APPROVED", "CHANGES_REQUESTED", "DISMISSED", "COMMENTED") or not isinstance(submitted, str) or not submitted or submitted > merged_at or not isinstance(review_commit, str) or not SHA.fullmatch(review_commit):
            raise RefreshError("ambiguous GitHub review evidence")
        previous = latest.get(login)
        if previous is None or submitted > previous[0]:
            latest[login] = (submitted, state, review_commit)
        elif submitted == previous[0] and (state, review_commit) != previous[1:]:
            raise RefreshError("ambiguous GitHub review evidence")
    approved = any(state == "APPROVED" and review_commit == head_sha
                   for _, state, review_commit in latest.values()) and not any(
        state in ("CHANGES_REQUESTED", "DISMISSED") for _, state, _ in latest.values())
    return {"repository": repository, "commit": commit,
            "base_repository": base_full_name, "base_ref": base_ref,
            "merged": bool(detail.get("merged_at")), "approved": approved,
            "pr_number": pr["number"], "head_commit": head_sha,
            "merge_commit": merge_sha}


def verify(repo, installed_commit, review_provider, *, fetcher=None):
    """Return (commit, manifest, source bytes) or fail before installation.

    review_provider(repository, commit) must query authenticated GitHub state
    independently and return exact merged PR and approval evidence.
    """
    repo = Path(repo)
    if not SHA.fullmatch(installed_commit or ""):
        raise RefreshError("installed package commit is not pinned")
    if git(repo, "remote", "get-url", "origin").decode().strip() != ORIGIN:
        raise RefreshError("public repository origin differs")
    if fetcher is None:
        git(repo, "fetch", "--quiet", "origin", "main")
    else:
        fetcher(repo)
    commit = git(repo, "rev-parse", "refs/remotes/origin/main").decode().strip()
    if not SHA.fullmatch(commit):
        raise RefreshError("invalid fetched main commit")
    git(repo, "merge-base", "--is-ancestor", installed_commit, commit)
    if commit == installed_commit:
        return commit, None, None
    if review_provider is None:
        raise RefreshError("trusted GitHub review evidence unavailable")
    evidence = review_provider(REPOSITORY, commit)
    if not isinstance(evidence, dict) or evidence.get("repository") != REPOSITORY or \
            evidence.get("commit") != commit or evidence.get("base_repository") != REPOSITORY or \
            evidence.get("base_ref") != "main" or \
            evidence.get("merged") is not True or evidence.get("approved") is not True or \
            not isinstance(evidence.get("pr_number"), int) or evidence["pr_number"] <= 0 or \
            evidence.get("merge_commit") != commit or \
            not isinstance(evidence.get("head_commit"), str) or \
            not SHA.fullmatch(evidence["head_commit"]) or evidence["head_commit"] == commit:
        raise RefreshError("reviewed merge provenance missing or ambiguous")
    # Include descendants while limiting package extraction to the paths this
    # updater owns. Shared root rules and security/ remain unrelated repo data.
    rows = git(repo, "ls-tree", "-r", "-z", commit).split(b"\0")
    tree = {}
    for row in rows:
        if not row:
            continue
        meta, path = row.split(b"\t", 1)
        mode, kind, obj = meta.decode().split()
        name = path.decode()
        if name != MANIFEST_NAME and not any(name.startswith(root) for root in PACKAGE_ROOTS):
            continue
        if kind != "blob" or mode not in ("100644", "100755"):
            raise RefreshError(f"unexpected source type: {name}")
        tree[name] = obj
    expected_package = set(EXPECTED) | set(SOURCE_ONLY) | {MANIFEST_NAME}
    if set(tree) != expected_package:
        raise RefreshError("public package tree file set differs")
    try:
        manifest = json.loads(git(repo, "show", f"{commit}:{MANIFEST_NAME}"))
    except (ValueError, UnicodeError) as exc:
        raise RefreshError("invalid source manifest JSON") from exc
    # A Git commit cannot include its own SHA in a committed manifest. The
    # fetched ref supplies the immutable commit; null is mandatory on disk.
    if manifest.get("source_commit") is not None:
        raise RefreshError("source manifest must leave commit unbound")
    manifest["source_commit"] = commit
    files = _manifest(manifest, REPOSITORY, commit)
    source_only = manifest.get("source_only")
    if not isinstance(source_only, dict) or set(source_only) != SOURCE_ONLY:
        raise RefreshError("source-only manifest file set differs")
    for name in SOURCE_ONLY:
        data = git(repo, "show", f"{commit}:{name}")
        if digest(data) != source_only[name]["sha256"]:
            raise RefreshError(f"source-only hash differs: {name}")
    source = {}
    for name in EXPECTED:
        data = git(repo, "show", f"{commit}:{name}")
        if digest(data) != files[name]["sha256"]:
            raise RefreshError(f"source hash differs: {name}")
        source[name] = data
    return commit, manifest, source
