from pathlib import Path
p = Path('translations/en/LC_MESSAGES/messages.po')
s = p.read_text(encoding='utf-8')
lines = s.splitlines()
new_lines = [ln for ln in lines if not ln.strip().startswith('#, fuzzy')]
p.write_text('\n'.join(new_lines)+"\n", encoding='utf-8')
print('Removed fuzzy markers from', p)
