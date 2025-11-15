from pathlib import Path
import re

p = Path('translations/vi/LC_MESSAGES/messages.po')
if not p.exists():
    print('File not found:', p)
    raise SystemExit(1)

s = p.read_text(encoding='utf-8')
# Replace msgstr "" (immediately after msgid block) with msgstr "<same as msgid>"
# We'll parse pairs robustly
pairs = re.findall(r'(msgid\s+"([\s\S]*?)")\s*\n(msgstr\s+"([\s\S]*?)")', s)
if not pairs:
    print('No msgid/msgstr pairs found (unexpected)')
    raise SystemExit(1)

out = s
count = 0
for full_msgid, inner_msgid, full_msgstr, inner_msgstr in pairs:
    # Normalize the strings (msgid in file may contain escaped newlines, keep as-is)
    if inner_msgstr.strip() == '':
        # create replacement: replace the first occurrence of this pair with msgstr "<inner_msgid>"
        replacement = full_msgid + '\nmsgstr "' + inner_msgid.replace('"','\\"') + '"'
        # Use re.sub to replace only the first occurrence of this exact block
        pattern = re.compile(re.escape(full_msgid) + r'\s*\n' + re.escape(full_msgstr), re.M)
        out, n = pattern.subn(replacement, out, count=1)
        if n:
            count += 1

if count > 0:
    p.write_text(out, encoding='utf-8')
    print(f'Filled {count} empty msgstr entries in vi PO with msgid values.')
else:
    print('No empty msgstr entries found to fill.')
