import os
import re
from pathlib import Path

_PYTHON_KEYWORDS = frozenset([
    "def", "class", "return", "import", "from", "pass", "self", "none", "true",
    "false", "if", "else", "elif", "for", "while", "try", "except", "with", "as",
    "in", "not", "and", "or", "is", "lambda", "yield", "raise", "break",
    "continue", "global", "assert",
])

_STOP_WORDS = frozenset([
    "the", "this", "that", "these", "those", "with", "have", "will", "from",
    "they", "them", "been", "were", "was", "are", "our", "your", "their",
    "which", "when", "what", "where", "how", "also", "into", "onto", "than",
    "then", "some", "each", "both", "other", "more", "most", "only", "very",
    "just", "much", "such", "over", "after", "before", "about", "above",
    "below", "between", "through", "during", "without", "within", "along",
    "following", "across", "behind", "beyond", "plus", "except", "but", "can",
    "should", "would", "could", "shall", "may", "might", "must", "need",
    "dare", "used", "able",
])

_DEFAULT_REPO = Path(__file__).resolve().parent.parent


def _extract_tokens(text: str) -> set:
    parts = re.split(r"[^a-zA-Z0-9]+", text)
    tokens = set()
    for p in parts:
        word = p.lower()
        if len(word) > 3 and not p.isdigit() and word not in _PYTHON_KEYWORDS and word not in _STOP_WORDS:
            tokens.add(word)
    return tokens


def calculate_drift(repo_path=None) -> dict:
    """
    Compute semantic drift between the latest git commit and .kiro/steering/ specs.

    Returns a dict with:
      diff_tokens, spec_tokens, new_tokens (sorted lists),
      drift_score (float), token_counts (dict), and optionally error (str).
    """
    if repo_path is None:
        repo_path = _DEFAULT_REPO
    repo_path = Path(repo_path).resolve()

    try:
        import git  # type: ignore
        repo = git.Repo(repo_path)

        # Need at least 2 commits to diff
        try:
            diff_text = repo.git.diff("HEAD~1", "HEAD")
        except git.GitCommandError:
            return {
                "diff_tokens": [],
                "spec_tokens": [],
                "new_tokens": [],
                "drift_score": 0.0,
                "token_counts": {"diff_count": 0, "spec_count": 0, "new_count": 0},
            }

        if not diff_text.strip():
            return {
                "diff_tokens": [],
                "spec_tokens": [],
                "new_tokens": [],
                "drift_score": 0.0,
                "token_counts": {"diff_count": 0, "spec_count": 0, "new_count": 0},
            }

        diff_tokens = _extract_tokens(diff_text)

        steering_dir = repo_path / ".kiro" / "steering"
        spec_text = ""
        if steering_dir.exists():
            for spec_file in steering_dir.iterdir():
                if spec_file.is_file():
                    try:
                        spec_text += spec_file.read_text(errors="replace") + "\n"
                    except Exception:
                        pass

        spec_tokens = _extract_tokens(spec_text)
        new_tokens = diff_tokens - spec_tokens
        drift_score = round(len(new_tokens) / max(len(diff_tokens), 1), 6)

        return {
            "diff_tokens": sorted(diff_tokens),
            "spec_tokens": sorted(spec_tokens),
            "new_tokens": sorted(new_tokens),
            "drift_score": drift_score,
            "token_counts": {
                "diff_count": len(diff_tokens),
                "spec_count": len(spec_tokens),
                "new_count": len(new_tokens),
            },
        }

    except Exception as exc:
        return {
            "diff_tokens": [],
            "spec_tokens": [],
            "new_tokens": [],
            "drift_score": -1.0,
            "token_counts": {"diff_count": 0, "spec_count": 0, "new_count": 0},
            "error": str(exc),
        }
