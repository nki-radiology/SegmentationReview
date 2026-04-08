# AGENT_GUIDE.md — Using LLMs Productively in This Repository

This guide is for contributors who want to use Claude, ChatGPT, GitHub Copilot, or any other LLM as part of their Git workflow on this project. LLMs are useful tools — but only if you know how to direct them and when to trust (or not trust) their output.

---

## The core principle

> **LLMs accelerate drafting. They do not replace understanding.**

You are responsible for every line in your commit. "The LLM wrote it" is not a valid explanation during code review.

---

## 1. Generating a commit message

### Setup

Stage your changes and get the diff:
```bash
git add SegmentationReview/SegmentationReview.py
git diff --staged
```

### Prompt

```
You are a senior software engineer. Write a Git commit message in
Conventional Commits format for the diff below.

Rules:
- Format: type(scope): short description
- Types: feat | fix | refactor | docs | test | chore | style | perf
- Scope (use one): review | loader | ui | ci | deps | tutorial | release
- Subject line ≤ 72 chars, imperative mood ("add" not "added")
- Blank line, then body explaining WHY (not what — the diff shows that)
- If the diff mixes multiple concerns, flag that the author should split commits

--- DIFF ---
<paste git diff --staged output here>
```

### Real example

**Diff (adding a docstring to `_construct_full_path`):**

```diff
-    def _construct_full_path(self, path):
-        if os.path.isabs(path):
-            return path
-        else:
-            return self.joinpath(self.directory, path)
+    def _construct_full_path(self, path):
+        """Resolve a potentially relative file path to an absolute path.
+
+        If the path is already absolute it is returned unchanged.
+        Otherwise it is joined with the currently selected directory.
+
+        Args:
+            path: File path string from a CSV mapping file.
+
+        Returns:
+            str: Absolute file path.
+        """
+        if os.path.isabs(path):
+            return path
+        else:
+            return self.joinpath(self.directory, path)
```

**What the LLM produces:**

```
docs(review): add docstring to _construct_full_path

Mapping CSV files can contain relative or absolute paths, but the
method's behaviour for each case was not documented. This clarifies
the contract for future contributors reading the file-loading logic.
```

**What you check before committing:**
- Is `docs` the right type? Yes — only the docstring changed.
- Is `review` the right scope? Yes — this is in the SegmentationReview widget.
- Does the body explain *why*? Yes — it explains what was ambiguous.
- Any hallucinated issue numbers? No — the LLM didn't add one.

This is ready to commit as-is.

---

## 2. Writing a PR description

### Setup

```bash
git log origin/develop..HEAD --oneline
git diff origin/develop...HEAD --stat
```

### Prompt

```
Write a GitHub Pull Request description for a change to the
SegmentationReview 3D Slicer extension (Python, clinical use).

Structure (use exactly this):

## Summary
1–2 sentences: what changed and why.

## How to verify
Numbered steps a reviewer can follow to confirm the change.
Be specific — reference file names and line numbers where helpful.

## Checklist
- [ ] Commits follow Conventional Commits
- [ ] No patient data or large binaries committed
- [ ] PR targets develop, not main

--- COMMITS ---
<paste git log --oneline output here>

--- CHANGED FILES ---
<paste git diff --stat output here>
```

### Real example

**Commits:**
```
b2d9f0a docs(review): add docstring to _construct_full_path
3a71bce docs(review): add docstring to _is_valid_extension
```

**LLM output:**

```markdown
## Summary
Adds docstrings to two undocumented private methods in `SegmentationReview.py`:
`_is_valid_extension` and `_construct_full_path`. Both methods are called
during file loading but previously had no documentation of their arguments,
return values, or behaviour on edge cases.

## How to verify
1. Check out this branch: `gh pr checkout <number>`
2. Open `SegmentationReview/SegmentationReview.py`
3. Confirm `_is_valid_extension` (~line 252) has a docstring listing accepted
   formats (.nii, .nii.gz, .nrrd) and a return type.
4. Confirm `_construct_full_path` (~line 254) has a docstring describing the
   relative vs absolute path behaviour.

## Checklist
- [x] Commits follow Conventional Commits
- [x] No patient data committed
- [x] PR targets develop, not main
```

**What you check before submitting:**
- Are the line numbers roughly right? Verify — LLMs don't always get these right.
- Is the "how to verify" actually verifiable? Step through it mentally.
- Did the LLM invent a "Closes #N"? Remove it if there's no linked issue.

---

## 3. Asking for a code review suggestion

Use an LLM to get a first opinion on code you're about to push — not as a substitute for a human reviewer, but as an early sanity check.

### Prompt

```
You are reviewing a pull request for a medical imaging Python project
(3D Slicer extension used clinically).

Look at this code snippet and suggest one concise review comment using
our convention:
- Prefix: [blocker] | [nit] | [suggestion]
- Quote the specific line
- Explain the concern
- Suggest a fix if possible

--- CODE ---
<paste the function or block here>

--- CONTEXT ---
This method is called during dataset loading. Results are displayed
directly to clinical staff. Any crash would interrupt a review session.
```

### Real example

**Code:**
```python
def overwrite_mask_clicked(self):
    self.segmentation_node = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLSegmentationNode')
    file_path = self.joinpath(self.directory, "t.seg.nrrd")
    ...
    try:
        os.remove(file_path)
    except:
        pass
```

**LLM output:**

```
[nit] `except: pass` (line ~244) silently swallows all exceptions,
including KeyboardInterrupt and SystemExit. If the file deletion fails
for an unexpected reason (permissions, wrong path), nothing is logged
and the failure is invisible.

Suggested fix:
```python
try:
    os.remove(file_path)
except OSError:
    logger.warning("Could not remove temporary file %s", file_path)
```
This makes the intent explicit and preserves a log trail.
```

**What you do with this:** Decide whether the LLM's concern is valid (it is here), then push a fix commit or open a discussion on the PR.

---

## 4. Splitting LLM output into logical commits

When you give an LLM a task ("improve the docstrings in this file"), it often returns a large block of changes. Don't commit it all at once.

### Workflow

```bash
# 1. Apply the LLM's changes to the file

# 2. Review every change with git diff
git diff SegmentationReview/SegmentationReview.py

# 3. Stage one logical change at a time using -p (patch mode)
git add -p SegmentationReview/SegmentationReview.py

# 4. Commit it with a focused message
git commit -m "docs(review): add docstring to _is_valid_extension"

# 5. Repeat for the next change
git add -p SegmentationReview/SegmentationReview.py
git commit -m "docs(review): add docstring to joinpath"
```

**Why this matters:** Reviewers can understand and approve one change at a time. A single "LLM updated everything" commit is hard to review and hard to revert if something is wrong.

---

## 5. What NOT to do

### Don't commit code you don't understand

If the LLM rewrites a method and you can't explain what the new version does — don't commit it. Ask the LLM to explain it first, then decide.

### Don't paste the full file for a small task

Give the LLM the relevant function, not 500 lines of context. Narrow context = more focused output.

### Don't trust hallucinated issue numbers

LLMs invent `Closes #42` references. Always verify that the issue exists before including it in a commit message.

### Don't commit exploratory output

LLMs often suggest multiple approaches. Delete the ones you're not using before committing.

### Don't write "AI-generated" as your PR description

The PR description should describe the change. Mentioning that you used an LLM is fine in conversation, but "Generated by ChatGPT" is not a substitute for "what changed and why."

---

## Quick reference

| Task | Command | LLM role |
|---|---|---|
| Commit message | `git diff --staged` → paste into LLM | Draft the message; you edit and own it |
| PR description | `git log` + `git diff --stat` → paste | Draft the description; you verify line numbers |
| Review comment | Paste a function + context | Draft the comment; you decide if it's valid |
| Rebase plan | `git log --oneline HEAD~N` → paste | Suggest pick/fixup/drop plan; you execute it |
| Understand a diff | `git show <sha>` → paste | Explain in plain language |
