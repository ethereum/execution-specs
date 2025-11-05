"""
Tool for adding words to the codespell whitelist sanely.
"""

import argparse
from pathlib import Path
from sys import stderr

DESCRIPTION = """
Add words to the codespell whitelist.txt file sanely.
"""

parser = argparse.ArgumentParser(
    prog="whitelist",
    description=DESCRIPTION,
)
parser.add_argument(
    "words", type=str, nargs="+", help="Words to be added to the whitelist"
)
parser.add_argument(
    "-v", "--verbose", action="store_true", help="Enable verbose output"
)


def find_project_root() -> Path:
    """Locate the root directory of this project."""
    # Search upwards from script location
    script_dir = Path(__file__).resolve().parent
    for parent in [script_dir, *script_dir.parents]:
        if (parent / "pyproject.toml").exists():
            return parent

    raise FileNotFoundError("Unable to locate project root directory!")


def main() -> int:
    """
    `whitelist` accepts any number of strings, adds them to the whitelist, then
    sorts the list and maintain visible sections for each leading character.

    Returns:
      - 0 on success
      - 1 on error

    """
    args = parser.parse_args()
    new_words = args.words
    verbose = args.verbose

    try:
        project_root = find_project_root()
        whitelist_file = project_root / "whitelist.txt"

        # Read existing whitelist (create empty list if file doesn't exist)
        existing_words = []
        with open(whitelist_file, "r+", encoding="utf-8") as f:
            content = f.read()
        existing_words = [w.strip() for w in content.split("\n") if w.strip()]

        if verbose:
            print(f"Adding {len(new_words)} new words: {new_words}")

        # Combine and remove duplicates
        all_words = set(existing_words + new_words)

        if verbose:
            print(f"Total unique entries: {len(all_words)}")

        # Sort alphabetically (case-insensitive, then case-sensitive)
        sorted_words = sorted(all_words, key=lambda w: (w.casefold(), w))

        # Add blank lines before each new letter
        words_with_separators: list[str] = []
        previous_letter = ""

        for word in sorted_words:
            current_letter = word[0].lower()

            if current_letter != previous_letter and words_with_separators:
                words_with_separators.append("")

            words_with_separators.append(word)
            previous_letter = current_letter

            if verbose:
                print(f"Added {word}")

        # Create the whitelist content
        whitelist_content = "\n".join(words_with_separators)

        # Write to whitelist file
        with open(whitelist_file, "w", encoding="utf-8") as f:
            f.write(whitelist_content)

        print(f"Successfully updated {whitelist_file}")

    except KeyboardInterrupt:
        print("Aborted manually.", file=stderr)
        return 1

    except Exception as err:
        print(f"Unknown error! {err}")
        return 1

    return 0


if __name__ == "__main__":
    main()
