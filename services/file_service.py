import pandas as pd
import os
import re

def _col_to_index(col_str):
    """Convert Excel-style column (A, B, AA) to 0-based index."""
    if not col_str:
        return None
    s = str(col_str).strip().upper()
    if s.isdigit():
        return max(0, int(s) - 1)
    idx = 0
    for ch in s:
        if 'A' <= ch <= 'Z':
            idx = idx * 26 + (ord(ch) - ord('A') + 1)
        else:
            return None
    return idx - 1

def _parse_range(range_str):
    """Parse Excel range like 'A1:O5' into (start_col, start_row, end_col, end_row).
    Returns tuple of (start_col_idx, start_row_idx, end_col_idx, end_row_idx) - all 0-based.
    """
    if not range_str:
        return None
    # Match pattern like A1:O5
    match = re.match(r'^([A-Z]+)(\d+):([A-Z]+)(\d+)$', range_str.strip().upper())
    if not match:
        return None
    start_col = _col_to_index(match.group(1))
    start_row = int(match.group(2)) - 1  # Convert to 0-based
    end_col = _col_to_index(match.group(3))
    end_row = int(match.group(4)) - 1
    return (start_col, start_row, end_col, end_row)

def read_text_from_range(path, ext, scan_range):
    """Read text from a specific scan_range.

    Args:
        path: File path
        ext: File extension
        scan_range: Dict with keys 'range' (e.g. 'A1:O5') and 'sheet_name' (optional)

    Returns:
        String containing text from the specified range, or None if range invalid
    """
    ext = ext.lower()

    if ext in ("xls", "xlsx"):
        range_str = scan_range.get('range')
        sheet_name = scan_range.get('sheet_name')

        if not range_str:
            return None

        parsed = _parse_range(range_str)
        if not parsed:
            return None

        start_col, start_row, end_col, end_row = parsed

        # Read Excel file
        if sheet_name:
            # If sheet_name is numeric string, treat as index (0-based)
            if str(sheet_name).isdigit():
                sheet_idx = int(sheet_name)
                df = pd.read_excel(path, sheet_name=sheet_idx, dtype=str, header=None)
            else:
                # Try by name first, fallback to first sheet if not found
                try:
                    df = pd.read_excel(path, sheet_name=sheet_name, dtype=str, header=None)
                except ValueError:
                    # Sheet name not found, use first sheet
                    df = pd.read_excel(path, sheet_name=0, dtype=str, header=None)
        else:
            # Read first sheet by index (works regardless of sheet name)
            df = pd.read_excel(path, sheet_name=0, dtype=str, header=None)

        # Extract range
        df = df.fillna("")
        df_range = df.iloc[start_row:end_row+1, start_col:end_col+1]

        # Convert to text
        parts = []
        for idx, row in df_range.iterrows():
            row_text = " ".join(str(val) for val in row.tolist() if str(val).strip())
            if row_text.strip():
                parts.append(row_text)

        return "\n".join(parts)

    elif ext == "csv":
        range_str = scan_range.get('range')
        if not range_str:
            return None

        parsed = _parse_range(range_str)
        if not parsed:
            return None

        start_col, start_row, end_col, end_row = parsed

        df = pd.read_csv(path, dtype=str, header=None)
        df = df.fillna("")
        df_range = df.iloc[start_row:end_row+1, start_col:end_col+1]

        parts = []
        for idx, row in df_range.iterrows():
            row_text = " ".join(str(val) for val in row.tolist() if str(val).strip())
            if row_text.strip():
                parts.append(row_text)

        return "\n".join(parts)

    else:
        # For text files, read entire content (range not applicable)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def read_file_to_text(path, ext):
    """Legacy function - reads entire file without range filtering.
    Used for backward compatibility.
    """
    ext = ext.lower()
    if ext in ("xls", "xlsx"):
        xls = pd.read_excel(path, sheet_name=None, dtype=str)
        parts = []
        for sname, df in xls.items():
            df = df.fillna("")
            parts.append(f"---{sname}---")
            parts.append("\n".join(df.astype(str).agg(" ".join, axis=1).tolist()))
        return "\n".join(parts)
    elif ext == "csv":
        df = pd.read_csv(path, dtype=str)
        df = df.fillna("")
        return "\n".join(df.astype(str).agg(" ".join, axis=1).tolist())
    else:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

def cleanup_file(path):
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
