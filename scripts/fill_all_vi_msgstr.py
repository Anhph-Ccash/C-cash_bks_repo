from pathlib import Path

p = Path('translations/vi/LC_MESSAGES/messages.po')
if not p.exists():
    print('File not found:', p)
    raise SystemExit(1)

lines = p.read_text(encoding='utf-8').splitlines()
out_lines = []
i = 0
filled = 0
n = len(lines)
while i < n:
    line = lines[i]
    if line.startswith('msgid'):
        # collect full msgid block (msgid + following quoted lines)
        msgid_block = [line]
        i += 1
        while i < n and lines[i].lstrip().startswith('"'):
            msgid_block.append(lines[i])
            i += 1
        # now expect msgstr
        if i < n and lines[i].startswith('msgstr'):
            msgstr_block = [lines[i]]
            i += 1
            while i < n and lines[i].lstrip().startswith('"'):
                msgstr_block.append(lines[i])
                i += 1
            # determine if msgstr is empty (only msgstr "")
            # msgstr_block[0] like: msgstr ""
            first = msgstr_block[0].strip()
            rest_cont = msgstr_block[1:]
            if first == 'msgstr ""' and len(rest_cont) == 0:
                # build inner msgid text by concatenating quoted string pieces
                parts = []
                for l in msgid_block:
                    # find first quote and last quote
                    idx = l.find('"')
                    if idx != -1:
                        piece = l[idx+1:]
                        if piece.endswith('"'):
                            piece = piece[:-1]
                        parts.append(piece)
                inner = ''.join(parts)
                # escape any double quotes in inner
                inner_escaped = inner.replace('"', '\\"')
                out_lines.extend(msgid_block)
                out_lines.append('msgstr "' + inner_escaped + '"')
                filled += 1
            else:
                out_lines.extend(msgid_block)
                out_lines.extend(msgstr_block)
        else:
            # Malformed file, just append what we have
            out_lines.extend(msgid_block)
    else:
        out_lines.append(line)
        i += 1

if filled > 0:
    p.write_text('\n'.join(out_lines) + '\n', encoding='utf-8')
    print(f'Filled {filled} empty msgstr entries in vi PO.')
else:
    print('No empty msgstr entries found to fill.')
