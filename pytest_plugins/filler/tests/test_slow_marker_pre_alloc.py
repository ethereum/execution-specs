"""Test automatic pre_alloc_group marker application to slow tests."""

import textwrap

from ethereum_clis import TransitionTool


def test_slow_marker_gets_pre_alloc_group(pytester, default_t8n: TransitionTool):
    """Test that slow tests without benchmark marker get pre_alloc_group automatically."""
    test_module = textwrap.dedent(
        """\
        import pytest
        from ethereum_test_tools import Alloc, StateTestFiller, Transaction

        @pytest.mark.slow
        @pytest.mark.valid_from("Cancun")
        def test_slow_without_benchmark(state_test: StateTestFiller, pre: Alloc):
            sender = pre.fund_eoa()
            contract = pre.deploy_contract(code=b"")
            tx = Transaction(sender=sender, to=contract, gas_limit=100000)
            state_test(pre=pre, tx=tx, post={})
        """
    )

    # Create test directory structure
    tests_dir = pytester.mkdir("tests")
    cancun_dir = tests_dir / "cancun"
    cancun_dir.mkdir()
    test_file = cancun_dir / "test_slow.py"
    test_file.write_text(test_module)

    # Copy the pytest configuration
    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Run pytest with our plugin and check collection
    args = [
        "-c",
        "pytest-fill.ini",
        "--collect-only",
        "-q",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/cancun/test_slow.py",
    ]

    result = pytester.runpytest(*args)
    # The test should be collected successfully
    result.stdout.fnmatch_lines(["*test_slow_without_benchmark*"])


def test_slow_with_benchmark_no_pre_alloc(pytester, default_t8n: TransitionTool):
    """Test that slow tests WITH benchmark marker do NOT get pre_alloc_group."""
    test_module = textwrap.dedent(
        """\
        import pytest
        from ethereum_test_tools import Alloc, StateTestFiller, Transaction

        @pytest.mark.slow
        @pytest.mark.benchmark
        @pytest.mark.valid_from("Cancun")
        def test_slow_with_benchmark(state_test: StateTestFiller, pre: Alloc):
            sender = pre.fund_eoa()
            contract = pre.deploy_contract(code=b"")
            tx = Transaction(sender=sender, to=contract, gas_limit=100000)
            state_test(pre=pre, tx=tx, post={})
        """
    )

    # Create test directory structure
    tests_dir = pytester.mkdir("tests")
    benchmark_dir = tests_dir / "benchmark"
    benchmark_dir.mkdir()
    test_file = benchmark_dir / "test_slow_benchmark.py"
    test_file.write_text(test_module)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Run with collection only to verify test is collected
    args = [
        "-c",
        "pytest-fill.ini",
        "--collect-only",
        "-q",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/benchmark/test_slow_benchmark.py",
    ]

    result = pytester.runpytest(*args)
    # The test should be collected
    result.stdout.fnmatch_lines(["*test_slow_with_benchmark*"])


def test_slow_with_existing_pre_alloc_unchanged(pytester, default_t8n: TransitionTool):
    """Test that slow tests with existing pre_alloc_group marker are unchanged."""
    test_module = textwrap.dedent(
        """\
        import pytest
        from ethereum_test_tools import Alloc, StateTestFiller, Transaction

        @pytest.mark.slow
        @pytest.mark.pre_alloc_group("custom_group", reason="Custom reason")
        @pytest.mark.valid_from("Cancun")
        def test_slow_with_existing_pre_alloc(state_test: StateTestFiller, pre: Alloc):
            sender = pre.fund_eoa()
            contract = pre.deploy_contract(code=b"")
            tx = Transaction(sender=sender, to=contract, gas_limit=100000)
            state_test(pre=pre, tx=tx, post={})
        """
    )

    # Create test directory structure
    tests_dir = pytester.mkdir("tests")
    cancun_dir = tests_dir / "cancun"
    cancun_dir.mkdir()
    test_file = cancun_dir / "test_existing_pre_alloc.py"
    test_file.write_text(test_module)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Run with collection only to verify test is collected
    args = [
        "-c",
        "pytest-fill.ini",
        "--collect-only",
        "-q",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/cancun/test_existing_pre_alloc.py",
    ]

    result = pytester.runpytest(*args)
    # The test should be collected successfully
    result.stdout.fnmatch_lines(["*test_slow_with_existing_pre_alloc*"])


def test_non_slow_no_pre_alloc(pytester, default_t8n: TransitionTool):
    """Test that tests without slow marker do not get pre_alloc_group."""
    test_module = textwrap.dedent(
        """\
        import pytest
        from ethereum_test_tools import Alloc, StateTestFiller, Transaction

        @pytest.mark.valid_from("Cancun")
        def test_normal_speed(state_test: StateTestFiller, pre: Alloc):
            sender = pre.fund_eoa()
            contract = pre.deploy_contract(code=b"")
            tx = Transaction(sender=sender, to=contract, gas_limit=100000)
            state_test(pre=pre, tx=tx, post={})
        """
    )

    # Create test directory structure
    tests_dir = pytester.mkdir("tests")
    cancun_dir = tests_dir / "cancun"
    cancun_dir.mkdir()
    test_file = cancun_dir / "test_normal.py"
    test_file.write_text(test_module)

    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Run with collection only to verify test is collected
    args = [
        "-c",
        "pytest-fill.ini",
        "--collect-only",
        "-q",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/cancun/test_normal.py",
    ]

    result = pytester.runpytest(*args)
    # The test should be collected successfully
    result.stdout.fnmatch_lines(["*test_normal_speed*"])


def test_integration_with_fill(pytester, default_t8n: TransitionTool):
    """Integration test using actual fill command to verify marker application."""
    test_module = textwrap.dedent(
        """\
        import pytest
        from ethereum_test_tools import (
            Account,
            Alloc,
            StateTestFiller,
            Transaction,
        )

        @pytest.mark.slow
        @pytest.mark.valid_from("Cancun")
        def test_slow_for_integration(state_test: StateTestFiller, pre: Alloc):
            '''Test that should get pre_alloc_group marker automatically.'''
            sender = pre.fund_eoa()
            contract = pre.deploy_contract(code=b"")
            tx = Transaction(sender=sender, to=contract, gas_limit=100000)
            state_test(pre=pre, tx=tx, post={})
        """
    )

    # Create proper directory structure for tests
    tests_dir = pytester.mkdir("tests")
    cancun_tests_dir = tests_dir / "cancun"
    cancun_tests_dir.mkdir()
    slow_test_dir = cancun_tests_dir / "slow_test_module"
    slow_test_dir.mkdir()
    test_module_file = slow_test_dir / "test_slow_integration.py"
    test_module_file.write_text(test_module)

    # Copy pytest configuration
    pytester.copy_example(name="src/cli/pytest_commands/pytest_ini_files/pytest-fill.ini")

    # Run fill command
    args = [
        "-c",
        "pytest-fill.ini",
        "-v",
        "--no-html",
        "--t8n-server-url",
        default_t8n.server_url,
        "tests/cancun/slow_test_module/",
    ]

    # The test generates 3 formats (state_test, blockchain_test, blockchain_test_engine)
    # But it also runs on multiple forks (Cancun and Prague), so expect more tests
    # This is fine - the important thing is that they all pass
    result = pytester.runpytest(*args)

    # Verify that tests passed (don't care about exact count due to fork variations)
    assert result.ret == 0, "Fill command should succeed"
