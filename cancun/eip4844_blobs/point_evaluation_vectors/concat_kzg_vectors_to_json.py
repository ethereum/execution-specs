"""
Helper script to concatenate all the point evaluation test data.yaml files in
a directory into a single JSON file for easier consumption in tests.
"""
import argparse
import json
from pathlib import Path

import yaml  # type: ignore


def gather_yaml_data(directory: Path):  # noqa: D103
    all_data = []

    # Loop through each directory in the main directory
    for sub_dir in sorted(directory.iterdir()):
        if sub_dir.is_dir():
            yaml_file_path = sub_dir / "data.yaml"

            # Check if data.yaml exists in the directory
            if yaml_file_path.exists():
                with yaml_file_path.open("r") as yaml_file:
                    yaml_data = yaml.safe_load(yaml_file)
                    # Append the data along with the directory name
                    all_data.append(
                        {
                            "input": yaml_data["input"],
                            "output": yaml_data["output"],
                            "name": sub_dir.name,
                        }
                    )
    return all_data


def main():  # noqa: D103
    parser = argparse.ArgumentParser(
        description="Concatenate the data from multiple data.yaml files into one JSON file."
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        required=True,
        help="Input directory containing the YAML files.",
    )
    parser.add_argument(
        "-o", "--output", type=Path, required=True, help="Path to the output JSON file."
    )

    args = parser.parse_args()
    data = gather_yaml_data(args.input)
    with args.output.open("w") as json_file:
        json.dump(data, json_file, indent=2)


if __name__ == "__main__":
    main()
