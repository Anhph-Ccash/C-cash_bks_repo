from pathlib import Path
p = Path('translations/vi/LC_MESSAGES/messages.po')
if not p.exists():
    print('File not found:', p)
    raise SystemExit(1)

bak = p.with_suffix('.po.bak')
if not bak.exists():
    bak.write_bytes(p.read_bytes())
    print('Backup written to', bak)

s = p.read_text(encoding='utf-8')
# Replace backslash-escaped quotes (\") with plain quotes (")
s2 = s.replace('\\"', '"')
# Also replace occurrences of '\\n' (two characters backslash+n) with '\\n' (keep as two chars) - no-op
# but ensure we don't produce actual newline characters; so do not replace '\n' to newline

if s2 != s:
    p.write_text(s2, encoding='utf-8')
    print('Fixed escaped quotes in vi PO')
else:
    print('No escaped quotes found; no changes made')
