# Module 2 — Branches

---

## What is a branch?

A branch is best understood as:

> A **separate line of work** that starts from a specific point in your project

When you create a branch, you are essentially saying:

> “Make a copy of the project at this moment, and let me continue working from there”

For example:

```text
main:    A ── B ── C
                    \
feature:             D ── E   ← HEAD
```

* The branch `feature` starts from commit **C**
* From that point on, it **develops independently**
* New commits (D, E) are added only to the `feature` branch
* The `main` branch remains unchanged

👉 You can think of a branch as:

* A **copy of the project at a certain moment**
* That then **goes its own way**

---

## Why do we use branches?

Branches allow you to work safely and in parallel.

### 1. Isolation (very important)

You can work on something new **without affecting the main code**

* Your changes do not break the main version
* Others can continue working independently

---

### 2. Experimentation

You can try things freely:

* Test new ideas
* Refactor code
* Explore solutions

If it does not work → you can simply discard the branch

---

### 3. Collaboration

Multiple people can work at the same time:

* Each person works on their own branch
* Changes are combined later

---

### 4. Clean history

Each branch can represent **one logical change**

* Easier to review
* Easier to understand later

---

## Mental model

Instead of thinking of one timeline, think of:

> Multiple parallel timelines that can later be combined

```text
main:     A ── B ── C
                     \
feature:              D ── E
```

---

## More realistic example (multiple branches)

In practice, you will often have multiple branches at the same time:

```text
main:      A ── B ── C
                      \
feature/ui:            D ── E
                       \
fix/loading-bug:        F
                       \
docs/readme-update:     G ── H
```

* `feature/ui` → working on a new interface
* `fix/loading-bug` → quick bug fix
* `docs/readme-update` → documentation changes

👉 All branches:

* Start from a known point (often `main` or `develop`)
* Move forward independently
* Can later be merged back

---

## Branch naming convention

We use lowercase kebab-case with a type prefix:

| Prefix      | When to use                            |
| ----------- | -------------------------------------- |
| `feature/`  | New functionality or improvement       |
| `fix/`      | Bug fixes                              |
| `refactor/` | Restructuring without behaviour change |
| `docs/`     | Documentation-only changes             |
| `chore/`    | CI, tooling, dependency updates        |

### Examples

* `feature/add-docstring-joinpath`
* `feature/improve-ui-segmentation-panel`
* `fix/handle-missing-nrrd-extension`
* `fix/crash-on-empty-input`
* `docs/update-install-instructions`
* `chore/update-dependencies`

---

## Creating and switching branches

```bash
# Create a new branch and switch to it
git switch -c feature/add-docstring-joinpath

# List all local branches
git branch

# Switch to an existing branch
git switch develop

# Switch back to previous branch
git switch -
```

---

## What you see in GitHub Desktop

GitHub Desktop makes branches very visible:

* Current branch is shown at the top (e.g. `main`)
* You can click it to:

  * Create a new branch
  * Switch between branches

<p align="center">
  <img width="70%" src="../pics/gui_branch_switch.png" alt="GitHub Desktop branch switch">
</p>

👉 Important:

* You are always working **on exactly one branch**
* All commits go to the currently selected branch

---

## Merging

At some point, you want to bring your work back into the main code.

```bash
git switch develop
git merge feature/add-docstring-joinpath
```

This combines both histories:

```text
main:     A ── B ── C ── F
                     \  /
feature:              D ── E
```

---

### Merge strategies

| Strategy     | What it does                             |
| ------------ | ---------------------------------------- |
| Fast-forward | Moves the branch pointer forward         |
| Merge commit | Creates a new commit combining histories |
| Squash merge | Combines all commits into one            |

We typically use **squash merge via GitHub**.

---

## Key concept to remember

> A branch lets you work safely without affecting the main code

You can always:

* Create a branch
* Work independently
* Merge it back when ready

---

## Next step

👉 Continue to **[03_remote_workflow.md](03_remote_workflow.md)**
