# Copyright (C) 2025 Ethereum Foundation
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Tool for adding words to the codespell whitelist sanely.
"""

import argparse

DESCRIPTION = """
Add words to the codespell whitelist sanely
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


def main() -> None:
    """
    `whitelist` accepts any number of strings, adds them to the whitelist, then
    sorts the list and maintain visible sections for each leading character.
    """
    args = parser.parse_args()
    new_words = args.words
    verbose = args.verbose

    whitelist_file = "whitelist.txt"

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

    # Sort alphabetically
    sorted_words = sorted(all_words, key=str.casefold)

    # Add blank lines before each new letter
    words_with_separators = []
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

    print(f"\nSuccessfully updated {whitelist_file}")


if __name__ == "__main__":
    main()
