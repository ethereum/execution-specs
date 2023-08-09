"""
Create the whitelist.txt file used by the flake8-spellcheck plugin.

We maintain our project dictionaries in separate files for convenience. This
script simply concatenates them into a single file for use by the plugin.

It's equivalent to the bash command:
bash -c 'cat .wordlist.txt .wordlist_python_pytest.txt .wordlist_opcodes.txt > whitelist.txt'

But is written in Python for use in tox to make it cross-platform.
"""

from pathlib import Path


def main():
    """
    Create the whitelist.txt file used by the flake8-spellcheck plugin.
    """
    paths = [
        Path(".wordlist.txt"),
        Path(".wordlist_python_pytest.txt"),
        Path(".wordlist_opcodes.txt"),
    ]
    with open("whitelist.txt", "w") as whitelist:
        for path in paths:
            with open(path) as wordlist:
                whitelist.write(wordlist.read())
                whitelist.write("\n")


if __name__ == "__main__":
    main()
