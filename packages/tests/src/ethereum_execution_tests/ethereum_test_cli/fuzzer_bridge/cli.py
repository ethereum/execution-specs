"""Command-line interface for the fuzzer bridge."""

import json
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, as_completed
from functools import partial
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Tuple

import click
from rich.progress import (
    BarColumn,
    Progress,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
)

from ethereum_clis import GethTransitionTool, TransitionTool

from .blocktest_builder import BlocktestBuilder


def count_json_files(start_path: Path) -> int:
    """Count JSON files in directory."""
    return sum(1 for _ in start_path.rglob("*.json"))


def get_input_files(input_path: Path) -> Generator[Path, None, None]:
    """Generate input file paths."""
    if input_path.is_file():
        yield input_path
    else:
        yield from input_path.rglob("*.json")


def generate_test_name(file_path: Path, index: int = 0) -> str:
    """Generate unique test name from file path."""
    stem = file_path.stem
    if index > 0:
        return f"fuzzer_{stem}_{index}"
    return f"fuzzer_{stem}"


def process_single_file(
    input_file: Path,
    output_path: Path,
    builder: BlocktestBuilder,
    fork: Optional[str],
    pretty: bool,
    quiet: bool,
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
    random_blocks: bool = False,
) -> Dict[str, Any]:
    """Process a single fuzzer output file."""
    with open(input_file) as f:
        fuzzer_data = json.load(f)

    # Override fork if specified
    if fork:
        fuzzer_data["fork"] = fork

    # Determine number of blocks
    if random_blocks:
        from .blocktest_builder import choose_random_num_blocks

        actual_num_blocks = choose_random_num_blocks(
            len(fuzzer_data.get("transactions", []))
        )
    else:
        actual_num_blocks = num_blocks

    # Build blocktest
    blocktest = builder.build_blocktest(
        fuzzer_data,
        num_blocks=actual_num_blocks,
        block_strategy=block_strategy,
        block_time=block_time,
    )
    test_name = generate_test_name(input_file)
    fixtures = {test_name: blocktest}

    # Write output
    output_file = output_path / f"{input_file.stem}.json"
    with open(output_file, "w") as f:
        if pretty:
            json.dump(fixtures, f, indent=2)
        else:
            json.dump(fixtures, f)

    if not quiet:
        click.echo(f"Generated: {output_file}", err=True)

    return fixtures


def process_single_file_worker(
    file_info: Tuple[Path, Path],
    fork: Optional[str],
    pretty: bool,
    merge: bool,
    evm_bin: Optional[Path],
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
    random_blocks: bool = False,
) -> Tuple[
    Optional[Tuple[Path, Dict[str, Any]]], Optional[Tuple[Path, Exception]]
]:
    """Process a single file in a worker process."""
    json_file_path, output_file = file_info

    # Create transition tool and builder for this worker
    t8n = (
        GethTransitionTool(binary=evm_bin) if evm_bin else GethTransitionTool()
    )
    builder = BlocktestBuilder(t8n)

    try:
        with open(json_file_path) as f:
            fuzzer_data = json.load(f)

        # Override fork if specified
        if fork:
            fuzzer_data["fork"] = fork

        # Determine number of blocks
        if random_blocks:
            from .blocktest_builder import choose_random_num_blocks

            actual_num_blocks = choose_random_num_blocks(
                len(fuzzer_data.get("transactions", []))
            )
        else:
            actual_num_blocks = num_blocks

        # Build blocktest
        blocktest = builder.build_blocktest(
            fuzzer_data,
            num_blocks=actual_num_blocks,
            block_strategy=block_strategy,
            block_time=block_time,
        )
        test_name = generate_test_name(json_file_path)
        fixtures = {test_name: blocktest}

        if not merge:
            # Write individual file preserving structure
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as f:
                if pretty:
                    json.dump(fixtures, f, indent=2)
                else:
                    json.dump(fixtures, f)

        return (json_file_path, fixtures), None
    except Exception as e:
        return None, (json_file_path, e)


def process_file_batch(
    file_batch: list[Tuple[Path, Path]],
    fork: Optional[str],
    pretty: bool,
    merge: bool,
    evm_bin: Optional[Path],
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
    random_blocks: bool = False,
) -> Tuple[list[Tuple[Path, Dict[str, Any]]], list[Tuple[Path, Exception]]]:
    """Process a batch of files in a worker process."""
    # Create transition tool per worker
    t8n = (
        GethTransitionTool(binary=evm_bin) if evm_bin else GethTransitionTool()
    )
    builder = BlocktestBuilder(t8n)

    results = []
    errors = []

    for json_file_path, rel_path in file_batch:
        try:
            with open(json_file_path) as f:
                fuzzer_data = json.load(f)

            # Override fork if specified
            if fork:
                fuzzer_data["fork"] = fork

            # Determine number of blocks
            if random_blocks:
                from .blocktest_builder import choose_random_num_blocks

                actual_num_blocks = choose_random_num_blocks(
                    len(fuzzer_data.get("transactions", []))
                )
            else:
                actual_num_blocks = num_blocks

            # Build blocktest
            blocktest = builder.build_blocktest(
                fuzzer_data,
                num_blocks=actual_num_blocks,
                block_strategy=block_strategy,
                block_time=block_time,
            )
            test_name = generate_test_name(json_file_path)
            fixtures = {test_name: blocktest}

            if not merge:
                # Write individual file preserving structure
                output_file = rel_path.with_suffix(".json")
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w") as f:
                    if pretty:
                        json.dump(fixtures, f, indent=2)
                    else:
                        json.dump(fixtures, f)

            results.append((json_file_path, fixtures))
        except Exception as e:
            errors.append((json_file_path, e))

    return results, errors


def process_directory_parallel(
    input_dir: Path,
    output_dir: Path,
    fork: Optional[str],
    pretty: bool,
    merge: bool,
    quiet: bool,
    evm_bin: Optional[Path],
    num_workers: Optional[int] = None,
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
    random_blocks: bool = False,
) -> None:
    """Process directory of fuzzer output files with parallel processing."""
    all_fixtures = {}

    # Collect all files to process
    files_to_process = []
    for json_file_path in get_input_files(input_dir):
        rel_path = json_file_path.relative_to(input_dir)
        output_file = output_dir / rel_path
        files_to_process.append((json_file_path, output_file))

    file_count = len(files_to_process)
    if file_count == 0:
        if not quiet:
            click.echo("No JSON files found to process.", err=True)
        return

    # Determine optimal number of workers
    if num_workers is None:
        num_workers = min(mp.cpu_count(), max(1, file_count // 10))

    success_count = 0
    error_count = 0

    with Progress(
        TextColumn("[bold cyan]{task.fields[filename]}", justify="left"),
        BarColumn(
            bar_width=None,
            complete_style="green3",
            finished_style="bold green3",
        ),
        TaskProgressColumn(),
        TextColumn("[dim]({task.fields[workers]} workers)[/dim]"),
        TimeElapsedColumn(),
        expand=True,
        disable=quiet,
    ) as progress:
        task_id = progress.add_task(
            "Processing",
            total=file_count,
            filename="Starting...",
            workers=num_workers,
        )

        # Process files individually in parallel (better progress tracking)
        process_func = partial(
            process_single_file_worker,
            fork=fork,
            pretty=pretty,
            merge=merge,
            evm_bin=evm_bin,
            num_blocks=num_blocks,
            block_strategy=block_strategy,
            block_time=block_time,
            random_blocks=random_blocks,
        )

        with ProcessPoolExecutor(max_workers=num_workers) as executor:
            # Submit all files to the pool
            futures_to_files = {
                executor.submit(process_func, file_info): file_info[0]
                for file_info in files_to_process
            }

            # Process completions as they happen for real-time progress
            for future in as_completed(futures_to_files):
                file_path = futures_to_files[future]

                # Update progress with current file
                rel_path = file_path.relative_to(input_dir)
                display_name = str(rel_path)
                if len(display_name) > 40:
                    display_name = "..." + display_name[-37:]

                try:
                    result, error = future.result()

                    if result:
                        success_count += 1
                        _, fixtures = result
                        if merge:
                            all_fixtures.update(fixtures)
                    elif error:
                        error_count += 1
                        error_file, exception = error
                        if not quiet:
                            progress.console.print(
                                f"[red]Error processing {error_file}: {exception}[/red]"
                            )

                    # Update progress bar
                    progress.update(
                        task_id,
                        advance=1,
                        filename=display_name,
                        workers=num_workers,
                    )

                except Exception as e:
                    error_count += 1
                    if not quiet:
                        progress.console.print(
                            f"[red]Worker error for {file_path}: {e}[/red]"
                        )
                    progress.update(task_id, advance=1, filename=display_name)

        # Write merged file if requested
        if merge and all_fixtures:
            merged_file = output_dir / "merged_fixtures.json"
            with open(merged_file, "w") as f:
                if pretty:
                    json.dump(all_fixtures, f, indent=2)
                else:
                    json.dump(all_fixtures, f)
            if not quiet:
                progress.console.print(
                    f"[green]Merged fixtures written to: {merged_file}[/green]"
                )

        # Final status
        if not quiet:
            emoji = "✅" if error_count == 0 else "⚠️"
            progress.update(
                task_id,
                completed=file_count,
                filename=f"Done! {success_count} succeeded, {error_count} failed {emoji}",
                workers=num_workers,
            )


def process_directory(
    input_dir: Path,
    output_dir: Path,
    builder: BlocktestBuilder,
    fork: Optional[str],
    pretty: bool,
    merge: bool,
    quiet: bool,
    num_blocks: int = 1,
    block_strategy: str = "distribute",
    block_time: int = 12,
    random_blocks: bool = False,
) -> None:
    """Process directory of fuzzer output files."""
    all_fixtures = {}
    file_count = count_json_files(input_dir) if not quiet else 0
    success_count = 0
    error_count = 0

    with Progress(
        TextColumn("[bold cyan]{task.fields[filename]}", justify="left"),
        BarColumn(
            bar_width=None,
            complete_style="green3",
            finished_style="bold green3",
        ),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        expand=True,
        disable=quiet,
    ) as progress:
        task_id = progress.add_task(
            "Processing", total=file_count, filename="..."
        )

        for json_file_path in get_input_files(input_dir):
            # Preserve directory structure
            rel_path = json_file_path.relative_to(input_dir)
            display_name = str(rel_path)
            if len(display_name) > 40:
                display_name = "..." + display_name[-37:]

            progress.update(task_id, advance=1, filename=display_name)

            try:
                with open(json_file_path) as f:
                    fuzzer_data = json.load(f)

                # Override fork if specified
                if fork:
                    fuzzer_data["fork"] = fork

                # Determine number of blocks
                if random_blocks:
                    from .blocktest_builder import choose_random_num_blocks

                    actual_num_blocks = choose_random_num_blocks(
                        len(fuzzer_data.get("transactions", []))
                    )
                else:
                    actual_num_blocks = num_blocks

                # Build blocktest
                blocktest = builder.build_blocktest(
                    fuzzer_data,
                    num_blocks=actual_num_blocks,
                    block_strategy=block_strategy,
                    block_time=block_time,
                )
                test_name = generate_test_name(json_file_path)

                if merge:
                    # Add to merged fixtures
                    all_fixtures[test_name] = blocktest
                else:
                    # Write individual file preserving structure
                    output_file = output_dir / rel_path.with_suffix(".json")
                    output_file.parent.mkdir(parents=True, exist_ok=True)
                    fixtures = {test_name: blocktest}
                    with open(output_file, "w") as f:
                        if pretty:
                            json.dump(fixtures, f, indent=2)
                        else:
                            json.dump(fixtures, f)

                success_count += 1

            except Exception as e:
                error_count += 1
                if not quiet:
                    progress.console.print(
                        f"[red]Error processing {json_file_path}: {e}[/red]"
                    )

        # Write merged file if requested
        if merge and all_fixtures:
            merged_file = output_dir / "merged_fixtures.json"
            with open(merged_file, "w") as f:
                if pretty:
                    json.dump(all_fixtures, f, indent=2)
                else:
                    json.dump(all_fixtures, f)
            if not quiet:
                progress.console.print(
                    f"[green]Merged fixtures written to: {merged_file}[/green]"
                )

        # Final status
        if not quiet:
            emoji = "✅" if error_count == 0 else "⚠️"
            progress.update(
                task_id,
                completed=file_count,
                filename=f"Done! {success_count} succeeded, {error_count} failed {emoji}",
            )


def batch_mode(
    fork: Optional[str],
    evm_bin: Optional[Path],
    pretty: bool,
    num_blocks: int,
    block_strategy: str,
    block_time: int,
    random_blocks: bool,
) -> None:
    """
    Persistent batch processing mode.

    Reads input/output pairs from stdin, processes each, and outputs status
    to stdout. Protocol:
    - INPUT (stdin): <input_json_path> <output_directory>
    - OUTPUT (stdout): DONE <generated_blocktest_path> or ERROR <error_message>
    """
    import sys
    import traceback

    # Pre-initialize transition tool and builder once for performance
    t8n: TransitionTool
    if evm_bin:
        t8n = GethTransitionTool(binary=evm_bin)
    else:
        t8n = GethTransitionTool()

    builder = BlocktestBuilder(t8n)

    # Write ready signal to stderr for debugging
    print(
        "Batch mode initialized. Ready to process files.",
        file=sys.stderr,
        flush=True,
    )

    while True:
        try:
            # Read line from stdin
            line = sys.stdin.readline()
            if not line:  # EOF
                break

            line = line.strip()
            if not line:
                continue

            # Parse input/output paths
            parts = line.split()
            if len(parts) != 2:
                print(f"ERROR: invalid input format: {line}", flush=True)
                continue

            input_path_str, output_dir_str = parts
            input_path = Path(input_path_str)
            output_dir = Path(output_dir_str)

            # Process the file
            try:
                # Read fuzzer input
                if not input_path.exists():
                    print(f"ERROR: file not found: {input_path}", flush=True)
                    continue

                with open(input_path) as f:
                    fuzzer_data = json.load(f)

                # Override fork if specified
                if fork:
                    fuzzer_data["fork"] = fork

                # Determine number of blocks
                if random_blocks:
                    from .blocktest_builder import choose_random_num_blocks

                    actual_num_blocks = choose_random_num_blocks(
                        len(fuzzer_data.get("transactions", []))
                    )
                else:
                    actual_num_blocks = num_blocks

                # Build blocktest (existing logic)
                blocktest = builder.build_blocktest(
                    fuzzer_data,
                    num_blocks=actual_num_blocks,
                    block_strategy=block_strategy,
                    block_time=block_time,
                )

                # Generate test name
                test_name = generate_test_name(input_path)
                fixtures = {test_name: blocktest}

                # Write output
                output_dir.mkdir(parents=True, exist_ok=True)
                input_stem = input_path.stem
                output_file = output_dir / f"{input_stem}.json"

                with open(output_file, "w") as f:
                    if pretty:
                        json.dump(fixtures, f, indent=2)
                    else:
                        json.dump(fixtures, f)

                # Report success (CRITICAL: must flush)
                print(f"DONE {output_file}", flush=True)

            except FileNotFoundError:
                print(f"ERROR: file not found: {input_path}", flush=True)
            except json.JSONDecodeError as e:
                print(f"ERROR: invalid JSON in {input_path}: {e}", flush=True)
                # Log full traceback to stderr for debugging
                traceback.print_exc(file=sys.stderr)
            except Exception as e:
                print(
                    f"ERROR: conversion failed for {input_path}: {e}",
                    flush=True,
                )
                # Log full traceback to stderr for debugging
                traceback.print_exc(file=sys.stderr)

        except KeyboardInterrupt:
            break
        except Exception as e:
            # Catch-all for unexpected errors in the main loop
            print(f"ERROR: unexpected error in batch loop: {e}", flush=True)
            traceback.print_exc(file=sys.stderr)


@click.command()
@click.argument(
    "input_path",
    type=click.Path(
        exists=True, dir_okay=True, file_okay=True, path_type=Path
    ),
    required=False,
)
@click.argument(
    "output_path",
    type=click.Path(dir_okay=True, file_okay=False, path_type=Path),
    required=False,
)
@click.option(
    "--fork",
    default=None,
    help="Override fork specified in fuzzer output",
)
@click.option(
    "--evm-bin",
    type=click.Path(exists=True, path_type=Path),
    help="Path to evm binary for transition tool",
)
@click.option(
    "--pretty",
    is_flag=True,
    help="Pretty-print JSON output",
)
@click.option(
    "--merge",
    is_flag=True,
    help="Merge all tests into a single output file",
)
@click.option(
    "--quiet",
    is_flag=True,
    help="Suppress progress output",
)
@click.option(
    "--parallel/--no-parallel",
    default=True,
    help="Enable/disable parallel processing (default: enabled)",
)
@click.option(
    "-n",
    "--workers",
    type=int,
    default=None,
    help="Number of parallel workers (default: auto-detect based on CPU count)",
)
@click.option(
    "-b",
    "--num-blocks",
    type=int,
    default=1,
    help="Number of blocks to generate from fuzzer input (default: 1)",
)
@click.option(
    "--block-strategy",
    type=click.Choice(["distribute", "first-block"]),
    default="distribute",
    help="Transaction distribution strategy: 'distribute' splits txs evenly, "
    "'first-block' puts all txs in first block (default: distribute)",
)
@click.option(
    "--block-time",
    type=int,
    default=12,
    help="Seconds between blocks (default: 12)",
)
@click.option(
    "--random-blocks",
    is_flag=True,
    help="Randomly choose number of blocks (1 to min(num_txs, 10))",
)
@click.option(
    "--batch",
    is_flag=True,
    help="Persistent batch mode: read file paths from stdin, output to stdout",
)
def main(
    input_path: Optional[Path],
    output_path: Optional[Path],
    fork: Optional[str],
    evm_bin: Optional[Path],
    pretty: bool,
    merge: bool,
    quiet: bool,
    parallel: bool,
    workers: Optional[int],
    num_blocks: int,
    block_strategy: str,
    block_time: int,
    random_blocks: bool,
    batch: bool,
) -> None:
    """
    Convert fuzzer output to valid blocktest fixtures.

    INPUT_PATH: Input JSON file or directory (not required in --batch mode)
    OUTPUT_PATH: Output directory for fixtures (not required in --batch mode)

    In batch mode (--batch), reads input/output pairs from stdin.
    """
    # Batch mode: persistent stdin/stdout processing
    if batch:
        batch_mode(
            fork=fork,
            evm_bin=evm_bin,
            pretty=pretty,
            num_blocks=num_blocks,
            block_strategy=block_strategy,
            block_time=block_time,
            random_blocks=random_blocks,
        )
        return

    # Standard mode: require input_path and output_path
    if input_path is None or output_path is None:
        raise click.UsageError(
            "INPUT_PATH and OUTPUT_PATH are required when not using --batch mode"
        )
    # Create transition tool
    t8n: TransitionTool
    if evm_bin:
        t8n = GethTransitionTool(binary=evm_bin)
    else:
        t8n = GethTransitionTool()

    # Create builder
    builder = BlocktestBuilder(t8n)

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Process input
    if input_path.is_file():
        # Single file processing
        process_single_file(
            input_path,
            output_path,
            builder,
            fork,
            pretty,
            quiet,
            num_blocks,
            block_strategy,
            block_time,
            random_blocks,
        )
    else:
        # Directory processing with optional parallel mode
        if parallel:
            process_directory_parallel(
                input_path,
                output_path,
                fork,
                pretty,
                merge,
                quiet,
                evm_bin,
                workers,
                num_blocks,
                block_strategy,
                block_time,
                random_blocks,
            )
        else:
            process_directory(
                input_path,
                output_path,
                builder,
                fork,
                pretty,
                merge,
                quiet,
                num_blocks,
                block_strategy,
                block_time,
                random_blocks,
            )


if __name__ == "__main__":
    main()
