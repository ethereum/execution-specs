# Grammar Manual Verification

Low-confidence grammar issues requiring human review.

Format (but don't add a codeblock for each item):

```markdown
- [ ] path/to/file.py:15-17 - "original text"
  Suggestion: "corrected text"
  Reason: brief explanation
```

---

<!-- Issues will be appended below by Claude Code -->

## Round 9: ecrecover.py, sha256.py, ripemd160.py, identity.py

- [x] src/ethereum/forks/*/vm/precompiled_contracts/ecrecover.py:11 - "Implementation of the ECRECOVER precompiled contract."
  Suggestion: "Implementation of the `ECRECOVER` precompiled contract."
  Reason: Style consistency - SHA256, RIPEMD160, and IDENTITY all use backticks around the function name in their module docstrings, but ECRECOVER does not. This affects all 24 fork copies of ecrecover.py.
