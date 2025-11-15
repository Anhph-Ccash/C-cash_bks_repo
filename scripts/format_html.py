"""
Script để format và clean up HTML files trong templates/
"""
import re
from pathlib import Path

def clean_html(content):
    """Clean up HTML formatting"""
    # Remove excessive blank lines (more than 2 consecutive)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)

    # Fix inconsistent indentation in Jinja blocks
    content = re.sub(r'{%\s+', '{% ', content)
    content = re.sub(r'\s+%}', ' %}', content)
    content = re.sub(r'{{\s+', '{{ ', content)
    content = re.sub(r'\s+}}', ' }}', content)

    # Remove trailing whitespace
    lines = content.split('\n')
    lines = [line.rstrip() for line in lines]
    content = '\n'.join(lines)

    # Ensure file ends with newline
    if content and not content.endswith('\n'):
        content += '\n'

    return content

def main():
    templates_dir = Path('e:/C-cash_bks_repo/templates')

    for html_file in templates_dir.glob('*.html'):
        print(f"Processing {html_file.name}...")

        # Read original content
        with open(html_file, 'r', encoding='utf-8') as f:
            original = f.read()

        # Clean content
        cleaned = clean_html(original)

        # Write back if changed
        if cleaned != original:
            with open(html_file, 'w', encoding='utf-8') as f:
                f.write(cleaned)
            print(f"  ✓ Formatted {html_file.name}")
        else:
            print(f"  - No changes needed for {html_file.name}")

if __name__ == '__main__':
    main()
    print("\n✅ HTML formatting complete!")
