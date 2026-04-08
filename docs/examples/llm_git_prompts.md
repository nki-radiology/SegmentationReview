# Worked Example: LLMs as a Git Co-pilot

LLMs can help at every point in the Git workflow. Below are concrete, copy-paste-ready prompts — each illustrated with a real example from `SegmentationReview/SegmentationReview.py`.

---

## 1. Writing a commit message from a diff

**When:** You've staged your changes and want a first-draft commit message.

```bash
git diff --staged
```

**Prompt:**

```
You are a senior software engineer. Write a Git commit message in
Conventional Commits format for the diff below.

Rules:
- Format: type(scope): short description
- Types: feat | fix | refactor | test | docs | chore | perf | style
- Scopes for this repo: review | loader | ui | ci | deps | tutorial | release
- Subject line: ≤ 72 characters, imperative mood ("add" not "added")
- Blank line after subject
- Body: 2–4 sentences explaining WHY (not what — the diff shows that)
- If the diff touches multiple logical concerns, note that the author
  should consider splitting into separate commits

--- DIFF ---
<paste here>
```

**Example diff (adding a docstring to `_is_valid_extension`):**

```diff
-    def _is_valid_extension(self, path):
-        return any(path.endswith(i) for i in [".nii", ".nii.gz", ".nrrd"])
+    def _is_valid_extension(self, path):
+        """Return True if the file path ends with a supported format.
+
+        Supported formats: .nii, .nii.gz, .nrrd
+
+        Args:
+            path: File path as a string.
+
+        Returns:
+            bool
+        """
+        return any(path.endswith(i) for i in [".nii", ".nii.gz", ".nrrd"])
```

**Good LLM output:**

```
docs(review): add docstring to _is_valid_extension

The method had no docstring, making it unclear what file formats
are accepted or what the return type is. This is the entry point
for format validation and is called in multiple places, so clear
documentation reduces the risk of callers passing unsupported paths.
```

**LLM output that needs editing:**

```
docs: Updated _is_valid_extension to include documentation
```

Problems: no scope, past tense, vague body. Edit to the version above.

**Review checklist before committing:**
- [ ] Is the `type` accurate? (Don't call a refactor a `feat`)
- [ ] Is the `scope` in our allowed list?
- [ ] Does the body explain *why*, not repeat the diff?
- [ ] Did the LLM hallucinate an issue number?

---

## 2. Writing a PR description

**When:** Your branch is ready and you're about to open a PR.

```bash
git log origin/develop..HEAD --oneline
git diff origin/develop...HEAD
```

**Prompt:**

```
Write a GitHub Pull Request description for a change to the
SegmentationReview 3D Slicer extension.

Use this structure exactly:

## Summary
1–2 sentences: what changed, why it was needed.

## How to verify
Numbered steps a reviewer can follow to confirm the change locally.
For documentation-only changes, this can be "open the file and
confirm the docstring is present and accurate."

## Checklist
- [ ] Commits follow Conventional Commits
- [ ] No patient data committed
- [ ] PR targets develop, not main

--- COMMITS ---
<paste git log --oneline output>

--- DIFF SUMMARY ---
<paste diff or summary>
```

**Example output:**

```markdown
## Summary
Adds docstrings to `_is_valid_extension` and `joinpath`, two private
helper methods that previously had no documentation. This makes the
accepted file formats and method contracts explicit for future contributors.

## How to verify
1. Check out the branch: `gh pr checkout <number>`
2. Open `SegmentationReview/SegmentationReview.py`
3. Confirm `_is_valid_extension` (line ~252) and `joinpath` (line ~248)
   both have docstrings describing args, return type, and accepted formats.

## Checklist
- [x] Commits follow Conventional Commits
- [x] No patient data committed
- [x] PR targets develop, not main
```

---

## 3. Generating a review comment

**When:** You're reviewing a colleague's PR and want to frame feedback clearly.

**Prompt:**

```
You are reviewing a pull request for a medical imaging Python project.
Look at this code snippet and suggest a concise, constructive review
comment using our convention:
- Prefix with [blocker], [nit], or [suggestion]
- Quote the specific line
- Explain the concern
- Suggest a fix if possible

--- CODE ---
<paste the relevant lines>

--- CONTEXT ---
This is a 3D Slicer extension used clinically for segmentation review.
The method is called by the file-loading logic to decide whether to
attempt loading a file.
```

**Example code to review:**

```python
def _is_valid_extension(self, path):
    return any(path.endswith(i) for i in [".nii", ".nii.gz", ".nrrd"])
```

**Example LLM output:**

```
[nit] `path.endswith(".nii")` will also match `.nii.gz` files if `.nii.gz`
appears later in the list — but since you're using `any()`, the first match
wins, which happens to work correctly here. Consider reordering to check
`.nii.gz` before `.nii`, or add a comment explaining the order dependency
to prevent future bugs if someone rearranges the list.
```

---

## 4. Explaining a confusing diff

**When:** You're trying to understand what a change does or why it was made.

**Prompt:**

```
Explain what this git diff does in plain language.
Focus on:
1. What behaviour changed (from → to)
2. What problem or improvement this likely addresses
3. Any risks or things a reviewer should double-check

--- DIFF ---
<paste here>
```

---

## 5. Generating an interactive rebase plan

**When:** You have messy WIP commits and want to clean them up before a PR.

```bash
git log --oneline HEAD~5
```

**Prompt:**

```
I have these git commits (oldest first) on a feature branch.
I want to clean them up before opening a PR using `git rebase -i`.

Suggest a rebase plan using:
- pick: keep as-is
- reword: keep but edit the message
- fixup: meld into previous, discard this message
- drop: remove entirely

Also suggest final commit messages in Conventional Commits format.

--- COMMITS (oldest first) ---
3a71bce docs(review): add docstring to _is_valid_extension
b2d9f0a wip
9c44d81 fix typo
e7a1c3f docs: add docstring to joinpath too
a1b2c3d forgot the return type
```

**Expected output:**

```
pick  3a71bce  → keep: docs(review): add docstring to _is_valid_extension
fixup b2d9f0a
fixup 9c44d81
fixup a1b2c3d
pick  e7a1c3f  → reword to: docs(review): add docstring to joinpath
```

---

## Golden rules when using LLMs for git tasks

1. **You own the output.** Read and edit everything before committing.
2. **LLMs don't know your codebase history.** They can't tell you which issue to reference or which design decision was made last sprint.
3. **LLMs hallucinate issue numbers.** Always verify any `#N` references.
4. **Use them for drafting, not deciding.** The LLM doesn't know if a change is truly safe or backwards-compatible — you do.
