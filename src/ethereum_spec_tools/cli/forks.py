"""
CLI tool that queries Ethereum hardfork information
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

try:
    from ethereum_spec_tools.forks import Hardfork
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from hardfork import Hardfork


def get_fork_by_index(forks: List[Hardfork], index: int) -> Optional[Hardfork]:
    """
    Get fork by index, where 0 being Frontier and -1 being the most recent.
    """
    if not forks:
        return None
    
    if index < 0:
        # Negative indexing: -1 is last, -2 is second last, etc.
        if abs(index) <= len(forks):
            return forks[index]
        else:
            return None
    else:
        # Positive indexing: 0 is first (Frontier), 1 is second, etc.
        if index < len(forks):
            return forks[index]
        else:
            return None

def format_fork_info(fork: Hardfork, format_type: str) -> str:
    """
    Format fork information based on the requested format type.
    """
    if format_type == "name":
        return fork.short_name
    elif format_type == "title":
        return fork.title_case_name
    elif format_type == "full-name":
        return fork.name
    elif format_type == "test-name":
        return f"test_{fork.short_name}"
    elif format_type == "criteria":
        return str(fork.criteria)
    elif format_type == "consensus":
        return fork.consensus.name.lower()
    else:
        return fork.short_name


def main() -> None:
    """
    Main entry point for the CLI.
    """
    parser = argparse.ArgumentParser(
        prog="ethereum-spec-forks",
        description="Query Ethereum hardfork information for testing and development",
    )
    
    group = parser.add_mutually_exclusive_group()
    
    group.add_argument(
        "-n", "--fork-number",
        type=int,
        help="Fork number (0=Frontier, -1=most recent, etc.)",
    )
    
    # Format options (mutually exclusive)
    format_group = parser.add_mutually_exclusive_group()
    
    format_group.add_argument(
        "--name",
        action="store_true",
        help="Output short name (default)",
    )
    
    format_group.add_argument(
        "--title",
        action="store_true",
        help="Output title case name",
    )
    
    format_group.add_argument(
        "--full-name",
        action="store_true",
        help="Output full module name",
    )
    
    format_group.add_argument(
        "--test-name",
        action="store_true",
        help="Output test name format",
    )
    
    format_group.add_argument(
        "--criteria",
        action="store_true",
        help="Output fork criteria",
    )
    
    format_group.add_argument(
        "--consensus",
        action="store_true",
        help="Output consensus type",
    )
    
    # Base path option for development
    parser.add_argument(
        "--base-path",
        type=Path,
        help="Base path to ethereum module (for development)",
    )
    
    args = parser.parse_args()
    
    try:
        forks = Hardfork.discover(base=args.base_path)
    except Exception as e:
        print(f"Error discovering forks: {e}", file=sys.stderr)
        sys.exit(1)
    
    if not forks:
        print("No forks found", file=sys.stderr)
        sys.exit(1)
    
    if args.fork_number is not None:
        fork = get_fork_by_index(forks, args.fork_number)
        if fork is None:
            print(f"Fork index {args.fork_number} not found", file=sys.stderr)
            sys.exit(1)
        
        if args.title:
            format_type = "title"
        elif args.full_name:
            format_type = "full-name"
        elif args.test_name:
            format_type = "test-name"
        elif args.criteria:
            format_type = "criteria"
        elif args.consensus:
            format_type = "consensus"
        else:
            format_type = "name"
        
        print(format_fork_info(fork, format_type))
        return
    
    parser.print_help()


if __name__ == "__main__":
    main()
