"""
Open Digital Frame -- Thumbnail loader with a disk cache

Load the folder thumbnails scaled to the size required by the
directory browser. The scaled images are saved into a cache
directory (~/.cache/open-digital-frame), so that the original
files are decoded only once. JPEG sources are cached as JPEG,
any other format is cached as PNG to preserve transparency.

Only QImage is used here, never QPixmap, so the functions can
be called from a worker thread.
"""

from PyQt5.QtCore import QSize
from PyQt5.QtGui import QImage, QImageReader

import hashlib
import os

__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2026 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.0.1"

CACHE_DIR = os.path.join(
    os.environ.get('XDG_CACHE_HOME', os.path.expanduser('~/.cache')),
    'open-digital-frame')
CACHE_VERSION = 'v1'            # bump to invalidate every cached thumbnail
LOSSY_EXTENSIONS = ('.jpg', '.jpeg')

def _cache_location(path, st, w, h):
    """ Return (cache file path, Qt format name) for a source file. """
    ext = os.path.splitext(path)[1].lower()
    if ext in LOSSY_EXTENSIONS:
        fmt, suffix = 'JPG', '.jpg'
    else:
        fmt, suffix = 'PNG', '.png'      # keeps transparency
    raw = '%s|%s|%d|%d|%dx%d' % (CACHE_VERSION, path, st.st_mtime_ns, st.st_size, w, h)
    key = hashlib.sha1(raw.encode('utf-8')).hexdigest()
    return os.path.join(CACHE_DIR, key[:2], key + suffix), fmt

def thumbnail_qimage(path, w, h):
    """ Return a w x h QImage (or None), using a disk cache.
        Thread-safe: it only uses QImage, never QPixmap. """
    try:
        st = os.stat(path)
    except OSError:
        return None
    cached, fmt = _cache_location(path, st, w, h)

    img = QImage(cached)
    if not img.isNull():
        return img

    reader = QImageReader(path)
    reader.setScaledSize(QSize(w, h))
    img = reader.read()
    if img.isNull():
        return None

    tmp = '%s.%d.tmp' % (cached, os.getpid())
    try:
        os.makedirs(os.path.dirname(cached), exist_ok=True)
        quality = 90 if fmt == 'JPG' else -1      # -1: PNG default compression
        if img.save(tmp, fmt, quality):
            os.replace(tmp, cached)               # atomic: no half-written files
    except OSError:
        pass                                      # read-only fs: run uncached
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return img
