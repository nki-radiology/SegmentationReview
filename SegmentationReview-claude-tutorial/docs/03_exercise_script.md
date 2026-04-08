# Exercise script

## Scenario
You are collaborating on `SegmentationReview`, a Slicer extension used daily in the department.

## Exercise A — First feature branch
1. Create `feature/review-checklist-panel`
2. Edit a documentation string or placeholder function in `src/segmentation_review/review_panel.py`
3. Commit with a precise message
4. Push branch
5. Open PR using the template

## Exercise B — Second commit on same branch
1. Add a small follow-up improvement
2. Create a second commit
3. Discuss whether the branch should later be squashed or kept as multiple commits

## Exercise C — Code review
Reviewer leaves comments on:
- naming
- missing edge case
- too-large function
- unclear comment

Author responds by:
- pushing an update commit, or
- performing interactive rebase to clean history before merge

## Exercise D — Rebase
1. Another participant merges a change into `main`
2. Update local `main`
3. Rebase feature branch onto `main`
4. Resolve conflict
5. Push with `--force-with-lease`

## Exercise E — Post-merge hygiene
- delete branch
- inspect history on `main`
- compare squash merge vs rebase merge vs merge commit
