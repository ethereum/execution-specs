# Grammar Check Task

You will create a PR to the `fix-grammar` branch of `danceratopz/execution-specs`. Your task is to process ONE unchecked item from the grammar checklist.

## Step 1: Setup

```bash
git fetch origin fix-grammar && git checkout fix-grammar && git pull origin fix-grammar
```

## Step 2: Find Task

Read `repo_subpaths_for_grammar_check.md`. Find the FIRST item with `[ ]` status.

## Step 3: Ensure Branch is Based on fix-grammar

Your branch must be based on fix-grammar (not main). Rebase if needed:

```bash
git rebase fix-grammar
```

**Verify**: Run `ls grammar_check_prompt.md` - if this file doesn't exist, run `git rebase fix-grammar`.

**CRITICAL: Stay on this branch for ALL remaining steps. Do NOT switch or rename branches.**

## Step 4: Process Files

Use Glob to find all files matching the item's pattern(s). For each file:

- **`.py` files**: Check only:
  - Docstrings (triple-quoted strings)
  - `#` comments
  - String messages in `print()`, exceptions, logging, and error messages
- **`.md` files**: Check prose content, skip code blocks

### What to Fix (HIGH confidence - edit directly)

1. Missing prepositions ("refer the" -> "refer to the", "comply the" -> "comply with the")
2. Clear subject-verb disagreement
3. Missing articles where clearly required
4. Double words ("the the", "is is")
5. Clear typos in words

### What to Flag (LOW confidence - append to manual verification)

1. Style preferences vs grammar
2. Technical term ambiguity
3. Sentence structure that might be intentional
4. Anything you're uncertain about

### What NOT to Fix

- Variable names, function names, class names, or any identifiers
- Any source code logic - only modify text inside strings/comments
- Technical terms that look like typos (e.g., "keccak", "modexp", "precompile")
- Abbreviated variable references in comments (e.g., "the tx", "the msg")
- When fixing parallel structure in docstrings (e.g., "Multiply...pushes"), match the style used by OTHER functions in the same file. If neighbors use "Adds", "Subtracts", use "Multiplies...pushes"
- Capitalization changes unless clearly wrong (don't "fix" consistent lowercase)

## Step 5: Update Manual Verification

Append LOW-confidence issues to `grammar_manual_verification.md` in this format:

```markdown
- [ ] path/to/file.py:15-17 - "original text"
  Suggestion: "corrected text"
  Reason: brief explanation
```

## Step 6: Format & Lint Check

Before committing, ensure your changes pass formatting checks:

**Line length**: Docstrings and comments must not exceed 79 characters. Ruff cannot auto-fix this for comments or docstrings, so manually wrap long lines.

Run linters on any modified .py files (use `uvx` for speed):

```bash
uvx ruff format
uvx ruff check --fix
```

## Step 7: Complete Task

Change `[ ]` to `[x]` for the item you processed in `repo_subpaths_for_grammar_check.md`.

Commit all changes:

```bash
git add -A && git commit -m "docs: fix grammar in {subpath description}"
```

Example: `docs: fix grammar in src/ethereum/forks/*/vm/instructions (arithmetic, comparison, bitwise)`

## Step 8: Push and Create PR

Rebase on latest fix-grammar and push:

```bash
git fetch origin fix-grammar && git rebase origin/fix-grammar
git push -u origin HEAD
```

Provide the PR creation link targeting `fix-grammar` (as clickable link, NOT in a code block):

https://github.com/danceratopz/execution-specs/compare/fix-grammar...{your-branch-name}?expand=1

And provide the PR title for copy-paste:

`docs: fix grammar in {subpath description}`

Example title: `docs: fix grammar in src/ethereum/forks/*/vm/instructions (arithmetic, comparison, bitwise)`

## What to Ignore

- Code syntax and variable names
- Technical terms, EIP numbers, hex values
- Content inside code blocks (``` or indented)
- URLs, file paths, and email addresses
- Intentional shorthand in inline code comments

## Important Rules

- **Do NOT switch branches** after Step 3 - all work happens on your created branch
- Be conservative - only fix clear grammatical errors, not style preferences
- When uncertain, flag for manual review instead of fixing
- Process ONLY ONE checklist item per session
- Include a summary at the end: "Fixed N issues in M files. Flagged K items for manual review."
