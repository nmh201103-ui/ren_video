"""Compatibility shim for deprecated stdlib imghdr on Python 3.13+.

Provides a minimal `what()` using Pillow for code expecting imghdr.
"""
from io import BytesIO
from typing import Optional

try:
    # If stdlib imghdr exists, import and re-export it
    import imghdr as _stdlib_imghdr  # type: ignore
    from imghdr import *  # type: ignore
    what = _stdlib_imghdr.what  # ensure attribute exists
except Exception:
    # Fallback for Python versions where imghdr is removed
    from PIL import Image

    def what(file: Optional[str] = None, h: Optional[bytes] = None) -> Optional[str]:
        """Return detected image format ('jpeg', 'png', ...) or None.

        - If `h` is provided, detect from bytes.
        - Else if `file` is a path, read and detect.
        """
        try:
            if h is not None:
                img = Image.open(BytesIO(h))
                img.verify()
                fmt = getattr(img, 'format', None)
                return fmt.lower() if fmt else None
            if file:
                with open(file, 'rb') as f:
                    img = Image.open(f)
                    img.verify()
                    fmt = getattr(img, 'format', None)
                    return fmt.lower() if fmt else None
        except Exception:
            return None
        return None
