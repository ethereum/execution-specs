# Adding a New Test

All test cases are located underneath the `tests` directory, which are then organized by fork. Each fork contains sub-directories containing test sub-categories.

```text
📁 execution-test-specs/
├─╴📁 tests/
|   ├── 📄 __init__.py
│   ├── 📁 cancun/
|   |    ├── 📄 __init__.py
│   |    └── 📁 eip4844_blobs/
|   |        ├── 📄 __init__.py
|   |        ├── 📄 test_blobhash_opcode.py
|   |        ├── 📄 test_excess_blob_gas.py
|   |        └── 📄 ...
|   ├── 📁 shanghai
|   |    ├── 📁 eip3651_warm_coinbase
|   |    |   ├── 📄 __init__.py
|   |    |   └── 📄 test_warm_coinbase.py
|   |    ├── 📁 eip3855_push0
|   |    |   ├── 📄 __init__.py
|   |    |   └── 📄 test_push0.py
|   |    ├── 📁...
|   |    ...
│   └── 📁 ...
```

Each category/sub-directory may have multiple Python test modules (`*.py`) which in turn may contain many test functions. The test functions themselves are always parametrized by fork (by the framework).

A new test can be added by either:

- Adding a new `test_` python function to an existing file in any of the existing category subdirectories within `tests`.
- Creating a new source file in an existing category, and populating it with the new test function(s).
- Creating an entirely new category by adding a subdirectory in `tests` with the appropriate source files and test functions.
