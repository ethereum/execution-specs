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

- [x] packages/testing/src/execution_testing/cli/pytest_commands/plugins/help/help.py:43-44 - "Show help options specific to the execute's command remote and exit."
  Suggestion: "Show help options specific to the execute remote command and exit."
  Reason: "the execute's command remote" has awkward grammar - "execute's" implies possession but the structure is unclear

- [x] packages/testing/src/execution_testing/cli/pytest_commands/plugins/help/help.py:49-50 - "Show help options specific to the execute's command hive and exit."
  Suggestion: "Show help options specific to the execute hive command and exit."
  Reason: Same issue as above - awkward possessive structure

- [x] packages/testing/src/execution_testing/cli/pytest_commands/plugins/help/help.py:55-56 - "Show help options specific to the execute's command recover and exit."
  Suggestion: "Show help options specific to the execute recover command and exit."
  Reason: Same issue as above - awkward possessive structure

- [x] packages/testing/src/execution_testing/cli/pytest_commands/plugins/help/help.py:61-62 - "Show help options specific to the execute's command eth_config and exit."
  Suggestion: "Show help options specific to the execute eth_config command and exit."
  Reason: Same issue as above - awkward possessive structure

- [x] packages/testing/src/execution_testing/cli/fillerconvert/verify_filled.py:37-40 - "Verify post hash of the refilled test against original: Regex the original d,g,v from the refilled test name. Find the post record for this d,g,v and the fork of refilled test."
  Suggestion: "Verify the post hash of the refilled test against the original. Extract the d,g,v from the refilled test name. Find the post record for this d,g,v and the fork of the refilled test."
  Reason: Multiple potential issues - "Regex" used informally as a verb, possible missing articles ("the original", "the refilled test")

- [x] packages/testing/src/execution_testing/specs/blockchain.py:167-168 - "This can be used in a test to explicitly skip a field in a block's RLP encoding. included in the (json) output when the model is serialized."
  Suggestion: "This can be used in a test to explicitly skip a field in a block's RLP encoding that would otherwise be included in the (json) output when the model is serialized."
  Reason: Sentence fragment - lowercase "included" after period has no subject. The sentence structure is broken.
