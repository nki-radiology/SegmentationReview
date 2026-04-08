# Worked Example: LLMs as a Git Co-pilot

LLMs can help at several points in the Git workflow. Here are concrete, copy-paste-ready prompts for each.

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
- Scope: one of: loader | exporter | ui | review | ci | deps | tutorial | tests
- Subject line: ≤ 72 characters, imperative mood ("add" not "added")
- Blank line after subject
- Body: 2–4 sentences explaining WHY (not what — the diff shows that)
- If the diff touches multiple logical concerns, note that the author
  should consider splitting into separate commits
- End with "Closes #N" if you see an issue number in comments or the diff

--- DIFF ---
<paste here>
```

**Review checklist before committing:**
- [ ] Is the `type` accurate? (Don't call a refactor a `feat`)
- [ ] Is the `scope` in our allowed list?
- [ ] Does the body explain *why*, not repeat the diff?
- [ ] Did the LLM hallucinate an issue number?

---

## 2. Writing a PR description

**When:** Your branch is ready and you're about to open a PR.

```bash
git log origin/develop..HEAD --oneline   # show commits in your branch
git diff origin/develop...HEAD           # full diff
```

**Prompt:**

```
Write a GitHub Pull Request description for a change to the
SegmentationReview 3D Slicer extension.

Use this structure exactly:

## Summary
1–2 paragraphs: what changed, why it was needed, any important
design decisions. Mention if it's backwards compatible.

## How to test
Numbered steps a reviewer can follow to verify the change locally.

## Checklist
- [ ] Tests added / updated
- [ ] Docstrings updated  
- [ ] CHANGELOG entry added
- [ ] No patient data committed
- [ ] CI passes locally

Reference the issue number if you can infer it.

--- COMMITS ---
<paste git log output>

--- DIFF SUMMARY ---
<paste a summary or the full diff>
```

---

## 3. Reviewing code and suggesting a review comment

**When:** You're reviewing a colleague's PR and want to frame feedback clearly.

**Prompt:**

```
You are reviewing a pull request for a medical imaging Python project.
Look at this code snippet and suggest a concise, constructive review
comment following our convention:
- Prefix with [blocker], [nit], or [suggestion]
- Be specific: quote the line, explain the concern
- Suggest a fix if possible

--- CODE ---
<paste the relevant lines>

--- CONTEXT ---
This function is called from the 3D Slicer UI, and the result is shown
directly to clinicians. Empty segment lists are a realistic input.
```

---

## 4. Explaining a confusing diff or git history

**When:** You're trying to understand why a change was made, or what a complicated diff does.

**Prompt:**

```
Explain what this git diff does in plain language.
Focus on:
1. What behaviour changed (from → to)
2. What edge case or bug this likely addresses
3. Any risks or things a reviewer should double-check

--- DIFF ---
<paste here>
```

---

## 5. Generating an interactive rebase plan

**When:** You have messy WIP commits and want to clean them up before a PR.

```bash
git log --oneline HEAD~6
```

**Prompt:**

```
I have these git commits (newest last) on a feature branch.
I want to clean them up before opening a PR using `git rebase -i`.

Suggest a rebase plan using these commands:
- pick: keep as-is
- reword: keep but edit the message
- squash: meld into previous, keep both messages
- fixup: meld into previous, discard this message
- drop: remove entirely

Also suggest final commit messages (Conventional Commits format)
for any picks/rewords.

--- COMMITS (oldest first) ---
3a71bce feat(exporter): stub JSON writer
b2d9f0a wip
9c44d81 fix typo in variable name
e7a1c3f add tests for JSON writer
a1b2c3d forgot to handle None case
d4e5f6a cleanup
```

**Expected output something like:**

```
pick  3a71bce  → reword to: feat(exporter): add JSON export format
fixup b2d9f0a
fixup 9c44d81
fixup a1b2c3d
fixup d4e5f6a
pick  e7a1c3f  → reword to: test(exporter): add unit tests for JSON export
```

---

## Golden rules when using LLMs for git tasks

1. **You own the output.** Read and edit everything before committing.
2. **LLMs don't know your codebase history.** They can't tell you which issue to reference or which design decision was made last sprint.
3. **LLMs hallucinate issue numbers.** Always verify any `#N` references.
4. **Use them for drafting, not deciding.** The LLM doesn't know if a change is truly backwards compatible — you do.
