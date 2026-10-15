"""Conservative hook classifier for recognizable gated operations only."""


def classify(command: str) -> str:
    """Return deny codes; empty means abstain, never authorize."""
    words = command.lower().split()
    if len(words) >= 2 and words[0] == "git" and words[1] == "push":
        return "git_push"
    if len(words) >= 2 and words[0] == "gh" and words[1] in {"api", "pr", "issue", "release", "repo"}:
        return "github_mutation_review"
    if any(x in words for x in ("sendmail", "mutt", "msmtp")):
        return "external_communication"
    if any(x in words for x in ("deploy", "publish", "apply")):
        return "external_effect_review"
    return ""
