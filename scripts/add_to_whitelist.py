#!/usr/bin/env python3

import sys
import os

def main():
    # Get words from command-line arguments
    new_words = sys.argv[1:]

    if not new_words:
        print("Usage: ./whitelist_manager.py <word1> <word2> <word3> ...")
        print("Example: ./whitelist_manager.py foo bar baz")
        sys.exit(1)

    whitelist_file = 'whitelist.txt'

    # Read existing whitelist (create empty list if file doesn't exist)
    existing_words = []
    if os.path.exists(whitelist_file):
        with open(whitelist_file, 'r', encoding='utf-8') as f:
            content = f.read()
        existing_words = [w.strip() for w in content.split('\n') if w.strip()]
        print(f"Read {len(existing_words)} existing entries from {whitelist_file}")
    else:
        print(f"Creating new {whitelist_file}")

    print(f"Adding {len(new_words)} new words: {new_words}")

    # Combine and deduplicate using set
    all_words = set(existing_words + new_words)

    print(f"Total unique entries: {len(all_words)}")

    # Sort alphabetically (case-insensitive)
    sorted_words = sorted(all_words, key=str.lower)

    # Add blank lines before each new letter
    words_with_separators = []
    previous_letter = ''

    for word in sorted_words:
        current_letter = word[0].lower()

        # If we're starting a new letter (and it's not the first word), add a blank line
        if current_letter != previous_letter and len(words_with_separators) > 0:
            words_with_separators.append('')

        words_with_separators.append(word)
        previous_letter = current_letter

    # Create the whitelist content
    whitelist_content = '\n'.join(words_with_separators)

    # Write to whitelist file
    with open(whitelist_file, 'w', encoding='utf-8') as f:
        f.write(whitelist_content)

    print(f"\nSuccessfully updated {whitelist_file}")

if __name__ == '__main__':
    main()
