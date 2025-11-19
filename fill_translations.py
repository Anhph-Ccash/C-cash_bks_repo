#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Complete translation synchronization script.
Fills empty translations with msgid and ensures both files are in sync.
"""

import re
from pathlib import Path

def read_po_file(file_path):
    """Read a .po file and return its raw content."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def fill_empty_translations(content):
    """
    Fill empty msgstr entries with their corresponding msgid.
    Handles multi-line msgstr entries.
    """
    lines = content.split('\n')
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Check if this is a msgid line
        if line.startswith('msgid "'):
            result.append(line)
            msgid_content = line[7:-1]  # Content between quotes
            i += 1

            # Check for multi-line msgid
            while i < len(lines) and lines[i].startswith('"'):
                msgid_content += '\n' + lines[i]
                result.append(lines[i])
                i += 1

            # Now we should have msgstr line(s)
            if i < len(lines) and (lines[i].startswith('msgstr "') or lines[i].startswith('#~')):
                if lines[i].startswith('#~'):
                    # Commented out entries - skip
                    result.append(lines[i])
                    i += 1
                    continue

                # This is the msgstr line
                if lines[i] == 'msgstr ""':
                    # Empty translation - fill it
                    result.append(f'msgstr "{msgid_content}"')
                    i += 1
                else:
                    # Non-empty translation - keep as is
                    result.append(lines[i])
                    i += 1
                    # Check for multi-line msgstr
                    while i < len(lines) and lines[i].startswith('"') and not lines[i].startswith('msgid'):
                        result.append(lines[i])
                        i += 1
        else:
            result.append(line)
            i += 1

    return '\n'.join(result)

def sync_translations():
    """Main synchronization function."""
    en_file = Path('translations/en/LC_MESSAGES/messages.po')
    vi_file = Path('translations/vi/LC_MESSAGES/messages.po')

    print("=== Translation Synchronization Started ===\n")

    # Read both files
    en_content = read_po_file(en_file)
    vi_content = read_po_file(vi_file)

    print(f"English file: {en_file}")
    print(f"Vietnamese file: {vi_file}\n")

    # Count empty translations before
    en_empty_before = en_content.count('\nmsgstr ""')
    vi_empty_before = vi_content.count('\nmsgstr ""')
    print(f"Empty translations BEFORE:")
    print(f"  English: {en_empty_before}")
    print(f"  Vietnamese: {vi_empty_before}\n")

    # Fill empty translations
    print("Filling empty translations...")
    en_new = fill_empty_translations(en_content)
    vi_new = fill_empty_translations(vi_content)

    # Count empty translations after
    en_empty_after = en_new.count('\nmsgstr ""')
    vi_empty_after = vi_new.count('\nmsgstr ""')
    print(f"\nEmpty translations AFTER:")
    print(f"  English: {en_empty_after} (reduced by {en_empty_before - en_empty_after})")
    print(f"  Vietnamese: {vi_empty_after} (reduced by {vi_empty_before - vi_empty_after})\n")

    # Write updated files
    print("Writing updated files...")
    with open(en_file, 'w', encoding='utf-8') as f:
        f.write(en_new)
    print(f"  Updated: {en_file}")

    with open(vi_file, 'w', encoding='utf-8') as f:
        f.write(vi_new)
    print(f"  Updated: {vi_file}")

    print("\n=== Synchronization Complete ===")
    print(f"Total empty entries filled: {(en_empty_before - en_empty_after) + (vi_empty_before - vi_empty_after)}")

if __name__ == '__main__':
    sync_translations()
