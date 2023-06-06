# Adding a New Test

All test cases are located in the `fillers` directory, which is composed of many subdirectories, each one represents a different test category. The sub-directories may contain sub-categories, if necessary.

```
📁 execution-test-specs/
├─╴📁 fillers/                   # test cases
│   ├── 📁 eips/
│   |    ├── 📁 eip4844/
|   |    |    ├── 📄 blobhash_opcode.py
|   |    |    └── 📄 excess_data_gas.py
|   |    ├── 📄 eip3855.py
|   |    └── 📄 eip3860.py
│   ├── 📁 example/
│   ├── 📁 security/
│   ├── 📁 vm/
│   ├── 📁 withdrawals/
│   └── 📁 ...
```

Each category/sub-directory may have multiple Python test modules (`*.py`) which in turn may contain many test functions. The test functions themselves are always parametrized by fork, although when new tests are added for a feature under development, they will only be valid for the fork under active development.

Look for a relevant test category and add new tests to this category, if appropriate.

A new test can be added by either:

- Adding a new `test_` python function to an existing file in any of the
  existing category subdirectories within `fillers`.
- Creating a new source file in an existing category, and populating it with
  the new test function(s).
- Creating an entirely new category by adding a subdirectory in
  `fillers` with the appropriate source files and test functions.
