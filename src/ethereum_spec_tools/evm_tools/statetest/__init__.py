"""
Execute state tests.
"""

import argparse
import json
import logging
import sys
from copy import deepcopy
from dataclasses import dataclass
from io import StringIO
from typing import Any, Dict, Iterable, List, Optional, TextIO

from ethereum.utils.hexadecimal import hex_to_bytes

from ..t8n import T8N
from ..t8n.t8n_types import Result
from ..utils import get_supported_forks


@dataclass
class TestCase:
    """
    A test case derived from the inputs common to all forks and a single
    post-state unique to a single fork.
    """

    path: str
    key: str
    index: int
    fork_name: str
    post: Dict
    pre: Dict
    env: Dict
    transaction: Dict


def read_test_cases(test_file_path: str) -> Iterable[TestCase]:
    """
    Given a path to a filled state test in JSON format, return all the
    `TestCase`s it contains.
    """
    with open(test_file_path) as test_file:
        tests = json.load(test_file)

    for key, test in tests.items():
        env = test["env"]
        if not isinstance(env, dict):
            raise TypeError("env not dict")

        pre = test["pre"]
        if not isinstance(pre, dict):
            raise TypeError("pre not dict")

        transaction = test["transaction"]
        if not isinstance(transaction, dict):
            raise TypeError("transaction not dict")

        for fork_name, content in test["post"].items():
            for idx, post in enumerate(content):
                if not isinstance(post, dict):
                    raise TypeError(f'post["{fork_name}"] not dict')

                yield TestCase(
                    path=test_file_path,
                    key=key,
                    index=idx,
                    fork_name=fork_name,
                    post=post,
                    env=env,
                    pre=pre,
                    transaction=transaction,
                )


def run_test_case(
    test_case: TestCase,
    t8n_extra: Optional[List[str]] = None,
    output_basedir: Optional[str | TextIO] = None,
) -> Result:
    """
    Runs a single general state test
    """
    from .. import create_parser

    env = deepcopy(test_case.env)
    try:
        env["blockHashes"] = {"0": env["previousHash"]}
    except KeyError:
        env["blockHashes"] = {}
    env["withdrawals"] = []

    alloc = deepcopy(test_case.pre)

    post = deepcopy(test_case.post)
    d = post["indexes"]["data"]
    g = post["indexes"]["gas"]
    v = post["indexes"]["value"]

    tx = {}
    for k, value in test_case.transaction.items():
        if k == "data":
            tx["input"] = value[d]
        elif k == "gasLimit":
            tx["gas"] = value[g]
        elif k == "value":
            tx[k] = value[v]
        elif k == "accessLists":
            if value[d] is not None:
                tx["accessList"] = value[d]
        else:
            tx[k] = value

    txs = [tx]

    in_stream = StringIO(
        json.dumps(
            {
                "env": env,
                "alloc": alloc,
                "txs": txs,
            }
        )
    )
    out_stream = StringIO()

    # Run the t8n tool
    t8n_args = [
        "t8n",
        "--input.alloc",
        "stdin",
        "--input.env",
        "stdin",
        "--input.txs",
        "stdin",
        "--state.fork",
        f"{test_case.fork_name}",
    ]

    if t8n_extra is not None:
        t8n_args.extend(t8n_extra)

    parser = create_parser()
    t8n_options = parser.parse_args(t8n_args)
    if output_basedir is not None:
        t8n_options.output_basedir = output_basedir

    t8n = T8N(t8n_options, out_stream, in_stream)
    t8n.apply_body()
    return t8n.result


def state_test_arguments(subparsers: argparse._SubParsersAction) -> None:
    """
    Adds the arguments for the statetest tool subparser.
    """
    statetest_parser = subparsers.add_parser(
        "statetest",
        help="Runs state tests from a file or from the standard input.",
    )

    statetest_parser.add_argument("file", nargs="?", default=None)
    statetest_parser.add_argument("--json", action="store_true", default=False)
    statetest_parser.add_argument(
        "--noreturndata",
        dest="return_data",
        action="store_false",
        default=True,
    )
    statetest_parser.add_argument(
        "--nostack", dest="stack", action="store_false", default=True
    )
    statetest_parser.add_argument(
        "--nomemory", dest="memory", action="store_false", default=True
    )


class _PrefixFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        output = super().format(record)
        return "\n".join("# " + x for x in output.splitlines())


class StateTest:
    """
    Run one or more state tests.
    """

    def __init__(
        self, options: Any, out_file: TextIO, in_file: TextIO
    ) -> None:
        self.file = options.file
        self.out_file = out_file
        self.in_file = in_file
        self.supported_forks = tuple(
            x.casefold() for x in get_supported_forks()
        )
        self.trace: bool = options.json
        self.memory: bool = options.memory
        self.stack: bool = options.stack
        self.return_data: bool = options.return_data

    def run(self) -> int:
        """
        Execute the tests.
        """
        logger = logging.getLogger("T8N")
        logger.setLevel(level=logging.INFO)
        stream_handler = logging.StreamHandler()
        formatter = _PrefixFormatter("%(levelname)s:%(name)s:%(message)s")
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

        if self.file is None:
            return self.run_many()
        else:
            return self.run_one(self.file)

    def run_one(self, path: str) -> int:
        """
        Execute state tests from a single file.
        """
        results = []
        for test_case in read_test_cases(path):
            if test_case.fork_name.casefold() not in self.supported_forks:
                continue

            t8n_extra: List[str] = []

            if self.trace:
                t8n_extra.append("--trace")

            if self.memory:
                t8n_extra.append("--trace.memory")
            else:
                t8n_extra.append("--trace.nomemory")

            if not self.stack:
                t8n_extra.append("--trace.nostack")

            if self.return_data:
                t8n_extra.append("--trace.returndata")
            else:
                t8n_extra.append("--trace.noreturndata")

            result = run_test_case(
                test_case,
                t8n_extra=t8n_extra,
                output_basedir=sys.stderr,
            )

            # Always output the state root on stderr (even with tracing
            # disabled) for the holiman/goevmlab integration.
            json.dump(
                {"stateRoot": "0x" + result.state_root.hex()},
                sys.stderr,
            )
            sys.stderr.write("\n")

            passed = hex_to_bytes(test_case.post["hash"]) == result.state_root
            result_dict = {
                "stateRoot": "0x" + result.state_root.hex(),
                "fork": test_case.fork_name,
                "name": test_case.key,
                "pass": passed,
            }

            if not passed:
                actual = result.state_root.hex()
                expected = test_case.post["hash"][2:]
                result_dict[
                    "error"
                ] = f"post state root mismatch: got {actual}, want {expected}"

            results.append(result_dict)

        json.dump(results, self.out_file, indent=4)
        self.out_file.write("\n")
        return 0

    def run_many(self) -> int:
        """
        Execute state tests from a line-delimited list of files provided from
        `self.in_file`.
        """
        for line in self.in_file:
            result = self.run_one(line[:-1])
            if result != 0:
                return result
        return 0
