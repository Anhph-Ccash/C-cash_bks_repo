import zipfile
import os

def _is_within_directory(directory, target):
    abs_directory = os.path.abspath(directory)
    abs_target = os.path.abspath(target)
    return os.path.commonpath([abs_directory]) == os.path.commonpath([abs_directory, abs_target])

def safe_extract_zip(zip_path, dest_dir, allowed_exts=None):
    """
    Safely extract zip to dest_dir. Returns list of extracted file paths.
    Skips files with extensions not in allowed_exts (if provided).
    """
    extracted = []
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for member in zf.infolist():
            # skip directories
            if member.is_dir():
                continue
            member_name = member.filename
            # sanitize path to avoid zip-slip
            target_path = os.path.join(dest_dir, os.path.normpath(member_name))
            if not _is_within_directory(dest_dir, target_path):
                # skip unsafe entry
                continue
            # ensure parent dir exists
            parent = os.path.dirname(target_path)
            if parent:
                os.makedirs(parent, exist_ok=True)
            # filter by extension if provided
            if allowed_exts:
                ext = os.path.splitext(member_name)[1].lstrip('.').lower()
                if ext not in allowed_exts:
                    # skip non-allowed types
                    continue
            with zf.open(member) as source, open(target_path, 'wb') as target:
                target.write(source.read())
            extracted.append(target_path)
    return extracted
