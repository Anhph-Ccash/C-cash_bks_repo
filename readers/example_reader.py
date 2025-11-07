import pandas as pd
import os
from .base_reader import BaseReader

class ExampleReader(BaseReader):
    def read(self, file_path, scan_ranges):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".xls", ".xlsx"):
            xls = pd.read_excel(file_path, sheet_name=None, dtype=str)
            data = []
            for sheet, df in xls.items():
                df = df.fillna("")
                rows = df.astype(str).agg(" | ".join, axis=1).tolist()
                data.append({"sheet": sheet, "rows": rows})
            return data
        else:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                return {"text": f.read()}