"""Conservative hook classifier for recognizable gated operations only."""


def classify(command: str) -> str:
    """Return deny codes; empty means abstain, never authorize."""
    words = command.lower().split()
    # Recognize git global options and the common -C worktree option. This is
    # only a conservative hook aid; shell syntax, wrappers and alternate tools
    # cannot be secured by text matching.
    if words and words[0] == "git":
        i = 1
        while i < len(words):
            if words[i] in {"-c", "--config-env", "-C", "--git-dir", "--work-tree", "--namespace"}:
                i += 2
            elif words[i].startswith("-"):
                i += 1
            else:
                break
        if i < len(words) and words[i] == "push":
            return "git_push"
    if len(words) >= 2 and words[0] == "gh" and words[1] in {"api", "pr", "issue", "release", "repo"}:
        return "github_mutation_review"
    if any(x in words for x in ("sendmail", "mutt", "msmtp")):
        return "external_communication"
    if any(x in words for x in ("deploy", "publish", "apply")):
        return "external_effect_review"
    return ""
