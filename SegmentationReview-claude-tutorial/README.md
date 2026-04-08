# SegmentationReview Git & GitHub Training Repo

A small training repository for technical colleagues who already code in Python and want to learn to work **professionally and structurally with Git and GitHub**.

This repo is intentionally not about implementing algorithms. It is about learning the workflow around:

- cloning and setting remotes
- status / diff / log
- making focused commits
- pushing and pulling
- creating and updating branches
- rebasing on `main`
- resolving conflicts
- opening and reviewing pull requests
- working with Issues, PR templates, and code review comments
- writing clean commit messages, especially when using LLMs

The domain context is a fictionalized version of a 3D Slicer extension called **SegmentationReview**, so the exercises feel realistic for the department.

## Recommended use

Use this repo in a 60–90 minute workshop with 2–4 people per group.

## Learning goals

After this workshop, participants should be able to:

1. Explain the difference between **Git** and **GitHub**.
2. Use a **feature branch workflow** instead of committing directly to `main`.
3. Keep a branch up to date with `main` using **rebase**.
4. Open a **pull request** with a clear description.
5. Review code and leave useful comments.
6. Write small, meaningful commits.
7. Use LLMs productively without polluting the history or codebase.

---

## Suggested workshop flow

### Part 1 — Core mental model

Discuss these objects first:

- **working tree**: your files on disk
- **staging area**: what will go into the next commit
- **commit**: a named snapshot
- **branch**: a movable pointer to a sequence of commits
- **remote**: hosted version of the repo on GitHub
- **pull request**: a proposal to merge one branch into another

### Part 2 — The essential day-to-day workflow

1. Clone the repo
2. Create a branch from `main`
3. Make a small change
4. Stage selectively
5. Commit with a useful message
6. Push the branch
7. Open a PR
8. Respond to review feedback
9. Rebase on updated `main`
10. Merge the PR

### Part 3 — Structured collaboration

Use:

- issue templates
- pull request template
- branch naming convention
- conventional, descriptive commit messages
- review comments focused on maintainability and behavior

---

## Branch naming convention

Use one of:

- `feature/<topic>`
- `fix/<topic>`
- `docs/<topic>`
- `refactor/<topic>`
- `chore/<topic>`

Examples:

- `feature/export-summary-panel`
- `fix/mask-overlay-opacity`
- `docs/setup-training`

---

## Commit guidelines

Good commits are:

- **small**
- **single-purpose**
- **readable without opening the diff title first**
- **safe to review independently**

Examples:

- `Add reviewer note when no segmentation is loaded`
- `Refactor status formatting into helper function`
- `Update PR template with validation checklist`

Avoid:

- `stuff`
- `changes`
- `wip`
- `LLM update`
- `fix everything`

---

## LLM usage guidelines

LLMs are helpful, but the human remains responsible for the repository.

### Good practice

- ask the LLM for **options**, not a giant dump
- review generated code before committing
- split LLM-generated output into **logical commits**
- rewrite generated comments/docstrings to match team style
- mention material AI assistance in the PR when relevant

### Bad practice

- committing code you do not understand
- one huge commit generated in a single shot
- keeping hallucinated dead code or fake TODOs
- accepting verbose comments that add no value

A simple PR note is enough:

> Drafted with LLM assistance, then manually reviewed and adapted.

---

## Suggested exercises

See:

- [`docs/01_workshop_plan.md`](docs/01_workshop_plan.md)
- [`docs/02_git_capabilities_map.md`](docs/02_git_capabilities_map.md)
- [`docs/03_exercise_script.md`](docs/03_exercise_script.md)
- [`docs/04_llm_and_commit_hygiene.md`](docs/04_llm_and_commit_hygiene.md)

---

## Minimal command set to practice

```bash
git clone <repo-url>
cd SegmentationReview-git-training

git switch -c feature/export-summary-panel
git status
git add <file>
git commit -m "Add export summary panel placeholder"
git push -u origin feature/export-summary-panel

git fetch origin
git rebase origin/main
git push --force-with-lease
```

Why `--force-with-lease` after rebase?
Because rebase rewrites commit history on your branch, and this is the safer way to update the remote PR branch.

---

## Nice external resources

Two strong supplements for this workshop are:

- **Learn Git Branching** for interactive visualization of branches, rebases, and remotes.
- **GitHub Skills** for small hands-on GitHub exercises such as pull requests and collaboration.

---

## Suggested repository setup on GitHub

Enable these in the GitHub repo settings:

- protect `main`
- require PR before merge
- require at least 1 review
- require checks to pass
- squash merge or rebase merge only
- delete head branches after merge

---

## Training scenario

The fake project is a Slicer extension with these possible branches:

- `feature/review-checklist-panel`
- `feature/export-csv-summary`
- `fix/empty-mask-warning`
- `refactor/status-helper`
- `docs/installation-notes`

These are intentionally scoped so participants can learn branching, reviews, rebasing, and merges without building a real feature-complete extension.
