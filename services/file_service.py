import pandas as pd
import os

def read_file_to_text(path, ext):
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
