# Git & GitHub capabilities map

This document is the "what is possible" overview.

## Local Git

### History and inspection
- `git status`
- `git diff`
- `git log`
- `git show`
- `git blame`
- selective staging with `git add -p`

### Branching
- create branch
- switch branch
- compare branches
- delete merged branches

### Integrating work
- merge
- rebase
- interactive rebase for squashing / rewording / reordering
- cherry-pick
- resolve conflicts
- stash temporary work

### Safety / recovery
- checkout old commits
- restore files
- revert commits
- reflog for recovery

## Remote collaboration

### Remote synchronization
- clone
- fetch
- pull
- push
- set upstream branch

### Collaboration workflow
- fork or shared repository workflows
- feature branches
- pull requests
- code review comments
- approvals / requested changes
- merge strategies

## GitHub platform features

### Repository hygiene
- branch protection
- CODEOWNERS
- PR template
- issue templates
- labels
- milestones

### Automation
- GitHub Actions checks
- lint / tests / formatting gates
- auto-close issues from PR descriptions

### Project organization
- issues
- discussions
- projects boards
- releases and tags

## Team behavior to teach explicitly
- do not commit directly to `main`
- keep branches short-lived
- prefer small PRs
- rebase before merge when policy requires it
- do not hide unrelated changes in one PR
- review for behavior, clarity, maintainability, and risk
