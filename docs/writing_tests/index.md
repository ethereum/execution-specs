# Writing Tests

The easiest way to get started is to use the interactive CLI:

```console
uv run eest make test
```

and modify the generated test module to suit your needs.

<figure class="video_container">
  <video controls="true" allowfullscreen="true">
    <source src="./img/eest_make_test.mp4" type="video/mp4">
  </video>
</figure>

For help deciding which test format to select, see [Types of Tests](./types_of_tests.md), in particular [Deciding on a Test Type](./types_of_tests.md#deciding-on-a-test-type). Otherwise, some simple test case examples to get started with are:

- [tests.berlin.eip2930_access_list.test_acl.test_account_storage_warm_cold_state](../tests/berlin/eip2930_access_list/test_acl/test_account_storage_warm_cold_state.md).
- [tests.istanbul.eip1344_chainid.test_chainid.test_chainid](../tests/istanbul/eip1344_chainid/test_chainid/test_chainid.md).

## Key Resources

- [Coding Standards](./code_standards.md) - Code style and standards for this repository
- [Adding a New Test](./adding_a_new_test.md) - Step-by-step guide to adding new tests
- [Writing a New Test](./writing_a_new_test.md) - Detailed guide on writing different test types
- [Using and Extending Fork Methods](./fork_methods.md) - How to use fork methods to write fork-adaptive tests
- [Gas Optimization](./gas_optimization.md) - Optimize gas limits in your tests for efficiency and compatibility with future forks.
- [Porting tests](./porting_legacy_tests.md): A guide to porting @ethereum/tests to EEST.

Please check that your code adheres to the repo's coding standards and read the other pages in this section for more background and an explanation of how to implement state transition and blockchain tests.
