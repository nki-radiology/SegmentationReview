# LLMs, comments, and commit hygiene

## Principle
LLMs accelerate drafting. They do not replace ownership.

## Review checklist for LLM-generated changes
- Do I understand the code path?
- Are names consistent with project style?
- Are comments concise and factual?
- Is the diff bigger than necessary?
- Can this be split into smaller commits?
- Is there any placeholder or hallucinated API?
- Does the PR explain what was generated and what was manually changed?

## Commit hygiene rules

### Rule 1
One purpose per commit.

### Rule 2
Commit messages should describe the change, not your activity.

### Rule 3
Do not commit exploratory or abandoned LLM output.

### Rule 4
If the LLM changed structure, mention the architectural intent in the PR.

## Comment hygiene rules
Good comments explain:
- why something exists
- assumptions
- non-obvious constraints

Bad comments restate obvious code.

## Example
Bad:
```python
# increment i
i += 1
```

Better:
```python
# Skip the first slice because it contains the calibration marker rather than anatomy.
i += 1
```
