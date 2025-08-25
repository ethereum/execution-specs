"""Simple CLI tool that reads filler files in the `ethereum/tests` format."""

import argparse
from glob import glob
from pathlib import Path

from .verify_filled import verify_refilled


def main() -> None:
    """Run the main function."""
    parser = argparse.ArgumentParser(description="Filler parser.")

    parser.add_argument(
        "mode", type=str, help="The type of filler we are trying to parse: blockchain/state."
    )
    parser.add_argument("folder_path", type=Path, help="The path to the JSON/YML filler directory")
    parser.add_argument("legacy_path", type=Path, help="The path to the legacy tests directory")

    args = parser.parse_args()
    args.folder_path = Path(str(args.folder_path).split("=")[-1])
    args.mode = str(args.mode).split("=")[-1]

    print("Scanning: " + str(args.folder_path))
    files = glob(str(args.folder_path / "**" / "*.json"), recursive=True) + glob(
        str(args.folder_path / "**" / "*.yml"), recursive=True
    )

    if args.mode == "blockchain":
        raise NotImplementedError("Blockchain filler not implemented yet.")

    if args.mode == "verify":
        verified_vectors = 0
        for file in files:
            print("Verify: " + file)
            refilled_file = file
            relative_file = file.removeprefix(str(args.folder_path))[1:]
            original_file = args.legacy_path / "GeneralStateTests" / relative_file
            verified_vectors += verify_refilled(Path(refilled_file), original_file)
        print(f"Total vectors verified: {verified_vectors}")

        # Solidity skipped tests
        # or file.endswith("stExample/solidityExampleFiller.yml")
        # or file.endswith("vmPerformance/performanceTesterFiller.yml")
        # or file.endswith("vmPerformance/loopExpFiller.yml")
        # or file.endswith("vmPerformance/loopMulFiller.yml")
        # or file.endswith("stRevertTest/RevertRemoteSubCallStorageOOGFiller.yml")
        # or file.endswith("stSolidityTest/SelfDestructFiller.yml")
