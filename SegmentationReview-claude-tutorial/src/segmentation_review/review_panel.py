"""Small placeholder module used for Git training exercises.

This file is intentionally simple. The goal is to create safe places where
participants can practice branching, commits, reviews, rebasing, and conflict
resolution without needing to implement real Slicer functionality.
"""


def get_review_summary(case_id: str, has_segmentation: bool) -> str:
    """Return a short status line for the training UI."""
    if not case_id:
        return "No case loaded"
    if not has_segmentation:
        return f"Case {case_id}: segmentation missing"
    return f"Case {case_id}: ready for review"
