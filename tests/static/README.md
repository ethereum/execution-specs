# Static Tests

This directory contains static test files that were originally located at [ethereum/tests](https://github.com/ethereum/tests/tree/develop/src). These files should not be modified directly.

## Important Policy

If you find a test that is broken or needs updating:

1. **DO NOT** modify the static test files directly.
2. Instead, create or update the corresponding Python test in the appropriate `tests/<fork>` folder.
3. Delete the original static test filler file(s).
4. Open a PR containing the new tests and the static tests deletion, and make sure that there is no coverage drop.
