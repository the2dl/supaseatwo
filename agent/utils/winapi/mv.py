# utils/winapi/mv.py

import os
import win32file
import shutil

def mv(src, dst):
    """Moves a file or directory from src to dst using Windows native APIs."""
    try:
        if not src or not dst:
            raise ValueError("Source and destination paths cannot be empty.")

        normalized_src = os.path.normpath(src)
        normalized_dst = os.path.normpath(dst)

        if not os.path.exists(normalized_src):
            raise FileNotFoundError(f"The source path '{normalized_src}' does not exist.")

        if os.path.isdir(normalized_dst):
            dst = os.path.join(normalized_dst, os.path.basename(normalized_src))

        shutil.move(normalized_src, normalized_dst)
        return f"Moved '{normalized_src}' to '{normalized_dst}'."
    except Exception as e:
        return f"Error moving file or directory: {str(e)}"