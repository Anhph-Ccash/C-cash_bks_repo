#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Synchronize translations between English and Vietnamese .po files.
"""

import re
from pathlib import Path
from datetime import datetime

def parse_po_file(file_path):
    """Parse a PO file and return entries as list of tuples."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    entries = []
    # Match both single-line and multi-line msgstr entries
    pattern = r'(#:.*?\nmsgid\s+"(.+?)"\nmsgstr\s+"(.*?)"\n)'

    for match in re.finditer(pattern, content, re.DOTALL):
        full_entry = match.group(1)
        msgid = match.group(2)
        msgstr = match.group(3)
        entries.append({
            'full': full_entry,
            'msgid': msgid,
            'msgstr': msgstr
        })

    return entries, content

def synchronize_translations():
    """Synchronize English and Vietnamese translation files."""
    en_file = Path('translations/en/LC_MESSAGES/messages.po')
    vi_file = Path('translations/vi/LC_MESSAGES/messages.po')

    print("=== Translation Synchronization ===\n")

    # Parse both files
    en_entries, en_content = parse_po_file(en_file)
    vi_entries, vi_content = parse_po_file(vi_file)

    print(f"English entries: {len(en_entries)}")
    print(f"Vietnamese entries: {len(vi_entries)}\n")

    # Create dictionaries by msgid for easy lookup
    en_dict = {e['msgid']: e for e in en_entries}
    vi_dict = {e['msgid']: e for e in vi_entries}

    # Find empty translations
    print("=== Empty Translations ===\n")
    en_empty = [(msgid, e['full']) for msgid, e in en_dict.items() if not e['msgstr'].strip()]
    vi_empty = [(msgid, e['full']) for msgid, e in vi_dict.items() if not e['msgstr'].strip()]

    print(f"Empty in English: {len(en_empty)}")
    for msgid, _ in en_empty[:5]:
        print(f"  - {msgid[:60]}")
    if len(en_empty) > 5:
        print(f"  ... and {len(en_empty) - 5} more\n")
    else:
        print()

    print(f"Empty in Vietnamese: {len(vi_empty)}")
    for msgid, _ in vi_empty[:5]:
        print(f"  - {msgid[:60]}")
    if len(vi_empty) > 5:
        print(f"  ... and {len(vi_empty) - 5} more\n")
    else:
        print()

    # Fill empty English translations with msgid
    print("=== Filling Empty English Translations ===\n")
    en_modified = False
    for msgid, _ in en_empty:
        en_dict[msgid]['msgstr'] = msgid
        en_modified = True
        print(f"Filled: {msgid[:70]}")

    if en_empty:
        print()

    # Fill empty Vietnamese translations with msgid
    print("=== Filling Empty Vietnamese Translations ===\n")
    vi_modified = False
    for msgid, _ in vi_empty:
        vi_dict[msgid]['msgstr'] = msgid
        vi_modified = True
        print(f"Filled: {msgid[:70]}")

    if vi_empty:
        print()

    # Rebuild files
    def rebuild_po_file(entries, original_content):
        """Rebuild PO file with updated entries."""
        result = original_content
        for entry in entries:
            # Replace old entry with new one
            old_entry = entry['full']
            new_entry = old_entry.replace(f'msgstr "{entry["msgstr"]}"', f'msgstr "{entry["msgstr"]}"')

            # Handle case where msgstr was empty
            if f'msgstr ""' in old_entry and entry['msgstr']:
                parts = old_entry.split('msgstr ""')
                new_entry = parts[0] + f'msgstr "{entry["msgstr"]}"\n'

            result = result.replace(old_entry, new_entry, 1)
        return result

    # Update the PO files
    if en_modified:
        # Rebuild English file entry by entry
        en_new_content = en_content
        header_end = en_new_content.find('#:')
        en_header = en_new_content[:header_end]

        en_new_entries = []
        for entry in en_entries:
            location_match = re.search(r'#:(.*?)\n', entry['full'])
            if location_match:
                location = location_match.group(1)
                en_new_entries.append(f'#:{location}\nmsgid "{entry["msgid"]}"\nmsgstr "{entry["msgstr"]}"\n')

        with open(en_file, 'w', encoding='utf-8') as f:
            f.write(en_header)
            f.write('\n'.join(en_new_entries))
        print(f"Updated: {en_file}")

    if vi_modified:
        # Rebuild Vietnamese file entry by entry
        vi_new_content = vi_content
        header_end = vi_new_content.find('#:')
        vi_header = vi_new_content[:header_end]

        vi_new_entries = []
        for entry in vi_entries:
            location_match = re.search(r'#:(.*?)\n', entry['full'])
            if location_match:
                location = location_match.group(1)
                vi_new_entries.append(f'#:{location}\nmsgid "{entry["msgid"]}"\nmsgstr "{entry["msgstr"]}"\n')

        with open(vi_file, 'w', encoding='utf-8') as f:
            f.write(vi_header)
            f.write('\n'.join(vi_new_entries))
        print(f"Updated: {vi_file}")

    print("\n=== Synchronization Complete ===")
    print(f"Files updated: {sum([en_modified, vi_modified])}")

if __name__ == '__main__':
    synchronize_translations()
