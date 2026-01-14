# Grammar Check

Audit grammar in documentation and code comments.

## Files to Check

Check `$ARGUMENTS` (default: `src/`). Use Glob to find:

- `**/*.py` - check docstrings and `#` comments only
- `**/*.md` - check prose content, skip code blocks

## What to Detect

1. Missing prepositions ("refer the" → "refer to the", "comply the" → "comply with the")
2. Subject-verb disagreement
3. Missing articles where required
4. Incorrect word order
5. Sentence fragments in documentation
6. Double words ("the the", "is is")

## What to Ignore

- Code syntax and variable names
- Technical terms, EIP numbers, hex values
- Intentional shorthand in inline code comments
- Content inside code blocks (``` or indented blocks in markdown)
- URLs and email addresses

## Output Format

For each issue, output a clickable link with line number:

```
path/to/file.md:42 - "original problematic text"
  Suggestion: "corrected text"
  Reason: brief explanation
```

For issues spanning multiple lines, use range format:

```
path/to/file.py:15-17 - "multi-line docstring issue"
  Suggestion: "corrected text"
  Reason: brief explanation
```

## Process

1. Find all matching files
2. For `.md` files: check full prose content, skip code blocks
3. For `.py` files: extract and check only docstrings (triple-quoted) and `#` comments
4. Group findings by file
5. End with summary: "Found N grammar issues in M files." or "No grammar issues found."

## Important

- Report findings only, do not auto-fix
- Be conservative: only flag clear errors, not style preferences
- When uncertain, skip rather than false-positive
