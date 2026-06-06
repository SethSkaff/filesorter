#!/usr/bin/env python3
"""
FileSorter — Native Desktop File Sorting Application
Built with PyQt6
"""

import sys
import os

# Must be set before any Qt import — fixes black-screen FFmpeg backend on Windows
os.environ.setdefault("QT_MEDIA_BACKEND", "windows")

import json
import shutil
import subprocess
import platform
import mimetypes
import tempfile
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog, QScrollArea, QTextEdit,
    QSplitter, QProgressBar, QStackedWidget, QFrame, QGridLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QDialog, QLineEdit, QMessageBox, QSlider, QSizePolicy,
    QGraphicsDropShadowEffect, QAbstractItemView, QComboBox,
    QListWidget, QListWidgetItem, QToolButton, QSpacerItem
)
from PyQt6.QtCore import (
    Qt, QSize, QRect, QPoint, QUrl, QThread, QObject, pyqtSignal, QTimer,
    QPropertyAnimation, QEasingCurve, QAbstractAnimation,
    QParallelAnimationGroup, pyqtProperty, QPointF, QRectF
)
from PyQt6.QtGui import (
    QPixmap, QImage, QFont, QColor, QPainter, QBrush, QPen,
    QLinearGradient, QIcon, QPalette, QShortcut, QKeySequence,
    QDesktopServices, QFontMetrics, QCursor, QTransform,
    QPainterPath, QRegion
)

try:
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    HAS_MULTIMEDIA = True
except ImportError:
    HAS_MULTIMEDIA = False

try:
    import fitz  # pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False

try:
    from pypdf import PdfReader
    HAS_PYPDF = True
except ImportError:
    HAS_PYPDF = False

try:
    import send2trash
    HAS_SEND2TRASH = True
except ImportError:
    HAS_SEND2TRASH = False

# ─── Platform ─────────────────────────────────────────────────────────────────

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"
FONT_FAMILY = "SF Pro Display" if IS_MAC else "Segoe UI"
MONO_FONT   = "SF Mono" if IS_MAC else "Cascadia Code"

# ─── Palette ──────────────────────────────────────────────────────────────────

C = {
    "bg":      "#1a1a2e",
    "panel":   "#16213e",
    "panel2":  "#0f3460",
    "accent":  "#4f8ef7",
    "del":     "#e05c5c",
    "keep":    "#4caf7d",
    "text":    "#ffffff",
    "text2":   "#8892a4",
    "border":  "#2a3a5e",
    "hover":   "#253555",
    "pressed": "#1a2a45",
}

# ─── File type sets ───────────────────────────────────────────────────────────

IMAGE_EXTS = {'.jpg','.jpeg','.png','.gif','.webp','.bmp','.tiff','.tif','.ico','.heic','.heif'}
VIDEO_EXTS = {'.mp4','.mov','.webm','.mkv','.avi','.m4v','.wmv','.flv','.ts'}
AUDIO_EXTS = {'.mp3','.m4a','.wav','.flac','.ogg','.aac','.wma','.opus','.aiff'}
PDF_EXTS   = {'.pdf'}
TEXT_EXTS  = {'.txt','.py','.js','.json','.csv','.md','.html','.css','.ts',
              '.jsx','.tsx','.xml','.yaml','.yml','.toml','.ini','.cfg','.sh',
              '.bat','.c','.cpp','.h','.java','.rs','.go','.rb','.php','.swift','.kt'}

SHORTCUT_KEYS = "123456789QWERTYUIOP"

SORT_ALPHA = "Alphabetically"
SORT_TYPE  = "By file type"
SORT_SIZE  = "By file size"
SORT_DATE  = "By date modified"
SORT_OPTIONS = [SORT_ALPHA, SORT_TYPE, SORT_SIZE, SORT_DATE]

MODE_SORT   = "sort"
MODE_SWIPE  = "swipe_only"

# ─── Global QSS ───────────────────────────────────────────────────────────────

GLOBAL_QSS = f"""
* {{ font-family: "{FONT_FAMILY}", system-ui, sans-serif; }}
QWidget {{ background: {C['bg']}; color: {C['text']}; font-size: 13px; }}
QMainWindow {{ background: {C['bg']}; }}
QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: {C['panel']}; width: 6px; border-radius: 3px; margin: 0;
}}
QScrollBar::handle:vertical {{
    background: {C['border']}; border-radius: 3px; min-height: 20px;
}}
QScrollBar::handle:vertical:hover {{ background: {C['text2']}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
QScrollBar:horizontal {{
    background: {C['panel']}; height: 6px; border-radius: 3px; margin: 0;
}}
QScrollBar::handle:horizontal {{
    background: {C['border']}; border-radius: 3px; min-width: 20px;
}}
QScrollBar::handle:horizontal:hover {{ background: {C['text2']}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}
QLineEdit {{
    background: {C['panel']}; border: 1.5px solid {C['border']};
    border-radius: 8px; padding: 8px 12px; color: {C['text']}; font-size: 13px;
}}
QLineEdit:focus {{ border-color: {C['accent']}; }}
QPushButton {{
    background: {C['panel']}; color: {C['text']};
    border: 1.5px solid {C['border']}; border-radius: 8px;
    padding: 8px 16px; font-size: 13px; font-weight: 500;
}}
QPushButton:hover {{ background: {C['hover']}; border-color: {C['accent']}; }}
QPushButton:pressed {{ background: {C['pressed']}; }}
QPushButton:disabled {{ color: {C['text2']}; border-color: {C['border']}; }}
QComboBox {{
    background: {C['panel']}; border: 1.5px solid {C['border']};
    border-radius: 8px; padding: 5px 10px; color: {C['text']}; font-size: 12px;
}}
QComboBox:hover {{ border-color: {C['accent']}; }}
QComboBox::drop-down {{ border: none; width: 20px; }}
QComboBox::down-arrow {{ width: 10px; height: 10px; }}
QComboBox QAbstractItemView {{
    background: {C['panel2']}; border: 1px solid {C['border']};
    selection-background-color: {C['hover']}; color: {C['text']};
    border-radius: 6px; padding: 4px;
}}
QProgressBar {{
    background: {C['panel']}; border: none; border-radius: 2px;
    max-height: 4px; text-align: center;
}}
QProgressBar::chunk {{ background: {C['accent']}; border-radius: 2px; }}
QTabWidget::pane {{
    background: {C['panel']}; border: 1px solid {C['border']}; border-radius: 8px;
}}
QTabBar::tab {{
    background: {C['bg']}; color: {C['text2']};
    padding: 8px 18px; border-top-left-radius: 8px; border-top-right-radius: 8px;
}}
QTabBar::tab:selected {{ background: {C['panel']}; color: {C['text']}; }}
QTabBar::tab:hover {{ color: {C['text']}; }}
QTableWidget {{
    background: {C['panel']}; gridline-color: {C['border']};
    border: none; border-radius: 8px;
}}
QTableWidget::item {{ padding: 8px; }}
QTableWidget::item:selected {{ background: {C['hover']}; }}
QHeaderView::section {{
    background: {C['panel2']}; color: {C['text2']};
    padding: 8px; border: none; font-weight: 600; font-size: 12px;
}}
QSplitter::handle {{ background: {C['border']}; width: 1px; height: 1px; }}
QTextEdit {{
    background: {C['panel']}; border: none; border-radius: 8px;
    padding: 12px; color: {C['text']};
    font-family: "{MONO_FONT}", "Consolas", monospace; font-size: 12px;
}}
QSlider::groove:horizontal {{
    background: {C['border']}; height: 4px; border-radius: 2px;
}}
QSlider::handle:horizontal {{
    background: {C['accent']}; width: 12px; height: 12px;
    margin: -4px 0; border-radius: 6px;
}}
QSlider::sub-page:horizontal {{ background: {C['accent']}; border-radius: 2px; }}
QLabel {{ background: transparent; }}
"""

# ─── Utility functions ────────────────────────────────────────────────────────

def fmt_size(b: int) -> str:
    for unit in ("B","KB","MB","GB","TB"):
        if b < 1024:
            return f"{b:.1f} {unit}" if unit != "B" else f"{b} B"
        b /= 1024
    return f"{b:.1f} PB"

def fmt_date(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%b %-d, %Y") if not IS_WIN else \
           datetime.fromtimestamp(ts).strftime("%b %d, %Y")

def file_type_label(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in IMAGE_EXTS: return "Image"
    if ext in VIDEO_EXTS: return "Video"
    if ext in AUDIO_EXTS: return "Audio"
    if ext in PDF_EXTS:   return "PDF"
    if ext in TEXT_EXTS:  return "Text / Code"
    return ext.upper().lstrip(".") + " File" if ext else "File"

def get_file_meta(path: Path) -> dict:
    try:
        stat = path.stat()
        return {
            "size":     stat.st_size,
            "modified": stat.st_mtime,
            "created":  stat.st_ctime,
        }
    except Exception:
        return {"size": 0, "modified": 0, "created": 0}

def collision_free(dst: Path) -> Path:
    if not dst.exists():
        return dst
    stem, suffix = dst.stem, dst.suffix
    parent = dst.parent
    i = 1
    while True:
        candidate = parent / f"{stem} ({i}){suffix}"
        if not candidate.exists():
            return candidate
        i += 1

def safe_move(src: Path, dst_folder: Path) -> Path:
    dst_folder.mkdir(parents=True, exist_ok=True)
    dst = collision_free(dst_folder / src.name)
    shutil.move(str(src), str(dst))
    return dst

def folder_size(path: Path) -> int:
    total = 0
    try:
        for p in path.rglob("*"):
            try:
                if p.is_file():
                    total += p.stat().st_size
            except Exception:
                pass
    except Exception:
        pass
    return total

def dir_file_count(path: Path) -> int:
    try:
        return sum(1 for p in path.iterdir() if p.is_file())
    except Exception:
        return 0

def dir_total_size(path: Path) -> int:
    try:
        return sum(p.stat().st_size for p in path.iterdir() if p.is_file())
    except Exception:
        return 0

# ─── Session persistence ──────────────────────────────────────────────────────

CONFIG_FILENAME = "sorter_config.json"

def load_session(folder: Path) -> dict | None:
    cfg = folder / CONFIG_FILENAME
    if cfg.exists():
        try:
            with open(cfg) as f:
                return json.load(f)
        except Exception:
            pass
    return None

def save_session(folder: Path, state: dict):
    cfg = folder / CONFIG_FILENAME
    try:
        with open(cfg, "w") as f:
            json.dump(state, f, indent=2)
    except Exception:
        pass

# ─── Worker threads ───────────────────────────────────────────────────────────

class ScanWorker(QObject):
    """Worker object moved to a QThread — never touches the UI directly."""
    batch_ready   = pyqtSignal(list)  # emits list of dicts, 50 at a time
    finished_scan = pyqtSignal()

    # Paths that lock up or take forever on Windows
    _SKIP_NAMES = frozenset({
        "System32", "WinSxS", "SysWOW64", "assembly", "servicing",
        "$Recycle.Bin", "System Volume Information", "WindowsApps",
        "MicrosoftEdgeBackups",
    })

    def __init__(self, root: "Path | None" = None):
        super().__init__()
        self.root     = root
        self._abort   = False

    def abort(self):
        self._abort = True

    def run(self):
        if self.root is None:
            if IS_MAC:
                roots = [Path("/Applications"), Path.home()]
            else:
                roots = [Path.home(),
                         Path("C:/Program Files"),
                         Path("C:/Program Files (x86)")]
        else:
            roots = [self.root]

        batch: list = []

        def flush():
            if batch:
                self.batch_ready.emit(list(batch))
                batch.clear()

        for root_path in roots:
            if self._abort:
                break
            try:
                for dirpath, dirnames, filenames in os.walk(
                        str(root_path), onerror=lambda e: None, followlinks=False):
                    if self._abort:
                        break
                    # Prune protected dirs in-place so os.walk skips them
                    dirnames[:] = [
                        d for d in dirnames
                        if d not in self._SKIP_NAMES
                        and not d.startswith(".")
                    ]
                    for fname in filenames:
                        if self._abort:
                            break
                        fpath = os.path.join(dirpath, fname)
                        try:
                            sz = os.path.getsize(fpath)
                            batch.append({"kind": "file", "path": fpath,
                                          "name": fname, "size": sz})
                        except (PermissionError, OSError):
                            continue
                        if len(batch) >= 50:
                            flush()
                    # Emit directories too (size 0 — computed on demand in UI)
                    for dname in dirnames:
                        batch.append({"kind": "dir",
                                      "path": os.path.join(dirpath, dname),
                                      "name": dname, "size": 0})
                    if len(batch) >= 50:
                        flush()
            except (PermissionError, OSError):
                pass

        flush()
        self.finished_scan.emit()


# Keep a thin QThread subclass so DiskAnalyzerDialog doesn't need extra plumbing
class DiskScanWorker(QThread):
    batch_ready   = pyqtSignal(list)
    finished_scan = pyqtSignal()

    def __init__(self, root: "Path | None" = None):
        super().__init__()
        self._worker = ScanWorker(root)
        self._worker.batch_ready.connect(self.batch_ready)
        self._worker.finished_scan.connect(self.finished_scan)
        self._worker.moveToThread(self)

    def abort(self):
        self._worker.abort()

    def run(self):
        self._worker.run()


class ThumbnailWorker(QThread):
    thumbnail_ready = pyqtSignal(int, QPixmap)  # index, pixmap

    def __init__(self, files: list, indices: list, size: int = 80):
        super().__init__()
        self.files = files
        self.indices = indices
        self.size = size
        self._abort = False

    def abort(self):
        self._abort = True

    def run(self):
        for idx in self.indices:
            if self._abort or idx >= len(self.files):
                break
            path = self.files[idx]
            ext = path.suffix.lower()
            pix = None
            try:
                if ext in IMAGE_EXTS:
                    qimg = QImage(str(path))
                    if not qimg.isNull():
                        pix = QPixmap.fromImage(qimg).scaled(
                            self.size, self.size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
                elif ext in PDF_EXTS and HAS_PYMUPDF:
                    doc = fitz.open(str(path))
                    if len(doc) > 0:
                        mat = fitz.Matrix(0.4, 0.4)
                        pg = doc[0].get_pixmap(matrix=mat)
                        img = QImage(pg.samples, pg.width, pg.height, pg.stride,
                                     QImage.Format.Format_RGB888)
                        pix = QPixmap.fromImage(img).scaled(
                            self.size, self.size,
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation)
                    doc.close()
            except Exception:
                pass
            if pix is None:
                pix = self._icon_pixmap(ext)
            self.thumbnail_ready.emit(idx, pix)

    def _icon_pixmap(self, ext: str) -> QPixmap:
        pix = QPixmap(self.size, self.size)
        pix.fill(QColor(C['panel2']))
        p = QPainter(pix)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(QColor(C['text2']))
        p.setFont(QFont(FONT_FAMILY, 10, QFont.Weight.Bold))
        label = ext.upper().lstrip(".")[:4] if ext else "FILE"
        p.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, label)
        p.end()
        return pix

# ─── Toast notification ───────────────────────────────────────────────────────

class Toast(QWidget):
    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        self._label = QLabel()
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"""
            background: rgba(30,40,70,0.95);
            color: {C['text']};
            border-radius: 20px;
            padding: 10px 22px;
            font-size: 13px;
            font-weight: 500;
            border: 1px solid {C['border']};
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self._label)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(250)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        self.hide()

    def show_message(self, msg: str, duration: int = 2000):
        self._label.setText(msg)
        self._label.adjustSize()
        self.adjustSize()
        self._reposition()
        self.setWindowOpacity(0)
        self.show()
        self.raise_()
        self._anim.stop()
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._timer.start(duration)

    def _fade_out(self):
        self._anim.stop()
        self._anim.setStartValue(1.0)
        self._anim.setEndValue(0.0)
        self._anim.finished.connect(self.hide)
        self._anim.start()

    def _reposition(self):
        p = self.parent()
        if p:
            pw, ph = p.width(), p.height()
            self.adjustSize()
            x = (pw - self.width()) // 2
            y = ph - self.height() - 32
            self.move(x, y)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self._reposition()

# ─── Folder pill button ───────────────────────────────────────────────────────

class FolderPillBtn(QPushButton):
    def __init__(self, name: str, shortcut: str, color: str = C['panel2'], parent=None):
        super().__init__(parent)
        self.folder_name = name
        self.shortcut_key = shortcut
        self._color = QColor(color)
        self._hover = False
        self.setFixedHeight(44)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.setStyleSheet("background: transparent; border: none; text-align: left;")
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)

        bg = self._color.lighter(120) if self._hover else self._color
        p.setBrush(QBrush(bg))
        p.setPen(QPen(QColor(C['accent']) if self._hover else QColor(C['border']), 1.5))
        p.drawRoundedRect(r, 22, 22)

        # Badge
        badge_rect = QRect(8, r.top() + (r.height() - 20) // 2, 24, 20)
        p.setBrush(QBrush(QColor(C['accent'])))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(badge_rect, 5, 5)
        p.setPen(QColor(C['text']))
        p.setFont(QFont(FONT_FAMILY, 9, QFont.Weight.Bold))
        p.drawText(badge_rect, Qt.AlignmentFlag.AlignCenter, self.shortcut_key)

        # Name
        p.setPen(QColor(C['text']))
        p.setFont(QFont(FONT_FAMILY, 12))
        name_rect = QRect(40, r.top(), r.width() - 48, r.height())
        metrics = QFontMetrics(p.font())
        text = metrics.elidedText(self.folder_name, Qt.TextElideMode.ElideRight, name_rect.width())
        p.drawText(name_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)
        p.end()

    def enterEvent(self, e):
        self._hover = True
        self.update()

    def leaveEvent(self, e):
        self._hover = False
        self.update()

# ─── Thumbnail strip ──────────────────────────────────────────────────────────

class ThumbnailStrip(QWidget):
    jumped = pyqtSignal(int)  # file index

    THUMB_W = 90
    THUMB_H = 70

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(self.THUMB_H + 16)
        self.setStyleSheet(f"background: {C['panel']}; border-top: 1px solid {C['border']};")
        self._files: list = []
        self._current_idx: int = 0
        self._thumbs: dict = {}  # index -> QPixmap
        self._worker: ThumbnailWorker | None = None

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 8, 8, 8)
        lay.setSpacing(6)

        self._prev_btn = QPushButton("‹")
        self._prev_btn.setFixedSize(28, self.THUMB_H)
        self._prev_btn.clicked.connect(self._scroll_prev)
        self._prev_btn.setStyleSheet(f"font-size:18px; background:{C['panel2']}; border-radius:6px;")

        self._next_btn = QPushButton("›")
        self._next_btn.setFixedSize(28, self.THUMB_H)
        self._next_btn.clicked.connect(self._scroll_next)
        self._next_btn.setStyleSheet(f"font-size:18px; background:{C['panel2']}; border-radius:6px;")

        self._scroll_area = QScrollArea()
        self._scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setFixedHeight(self.THUMB_H)
        self._scroll_area.setStyleSheet("background: transparent;")

        self._inner = QWidget()
        self._inner.setStyleSheet("background: transparent;")
        self._inner_lay = QHBoxLayout(self._inner)
        self._inner_lay.setContentsMargins(0, 0, 0, 0)
        self._inner_lay.setSpacing(6)
        self._scroll_area.setWidget(self._inner)

        lay.addWidget(self._prev_btn)
        lay.addWidget(self._scroll_area, 1)
        lay.addWidget(self._next_btn)

    def set_files(self, files: list, current_idx: int):
        self._files = files
        self._current_idx = current_idx
        self._thumbs.clear()
        self._rebuild_cells()
        self._load_thumbs()

    def update_current(self, idx: int):
        self._current_idx = idx
        self._rebuild_cells()
        self._load_thumbs()
        self._scroll_to_current()

    def _visible_range(self):
        start = max(0, self._current_idx - 1)
        end   = min(len(self._files), self._current_idx + 7)
        return list(range(start, end))

    def _rebuild_cells(self):
        while self._inner_lay.count():
            item = self._inner_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        visible = self._visible_range()
        for i in visible:
            cell = _ThumbCell(i, self._files[i] if i < len(self._files) else None,
                              i == self._current_idx, self._thumbs.get(i))
            cell.setFixedSize(self.THUMB_W, self.THUMB_H)
            cell.clicked_idx.connect(self.jumped)
            self._inner_lay.addWidget(cell)
        self._inner_lay.addStretch()
        self._inner.adjustSize()

    def _load_thumbs(self):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(200)
        visible = self._visible_range()
        needed  = [i for i in visible if i not in self._thumbs]
        if not needed:
            return
        files_list = [self._files[i] for i in needed if i < len(self._files)]
        self._worker = ThumbnailWorker(self._files, needed, size=self.THUMB_W)
        self._worker.thumbnail_ready.connect(self._on_thumb)
        self._worker.start()

    def _on_thumb(self, idx: int, pix: QPixmap):
        self._thumbs[idx] = pix
        self._rebuild_cells()

    def _scroll_to_current(self):
        visible = self._visible_range()
        if self._current_idx in visible:
            pos = visible.index(self._current_idx)
            self._scroll_area.horizontalScrollBar().setValue(
                pos * (self.THUMB_W + 6))

    def _scroll_prev(self):
        sb = self._scroll_area.horizontalScrollBar()
        sb.setValue(max(0, sb.value() - self.THUMB_W))

    def _scroll_next(self):
        sb = self._scroll_area.horizontalScrollBar()
        sb.setValue(sb.value() + self.THUMB_W)


class _ThumbCell(QWidget):
    clicked_idx = pyqtSignal(int)

    def __init__(self, idx, path, active, pixmap=None):
        super().__init__()
        self._idx = idx
        self._path = path
        self._active = active
        self._pixmap = pixmap
        self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.clicked_idx.emit(self._idx)

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        r = self.rect().adjusted(1, 1, -1, -1)
        bg = QColor(C['accent']).darker(120) if self._active else QColor(C['panel2'])
        pen_color = QColor(C['accent']) if self._active else QColor(C['border'])
        p.setBrush(QBrush(bg))
        p.setPen(QPen(pen_color, 1.5))
        p.drawRoundedRect(r, 8, 8)

        if self._pixmap:
            scaled = self._pixmap.scaled(r.width() - 4, r.height() - 4,
                                         Qt.AspectRatioMode.KeepAspectRatio,
                                         Qt.TransformationMode.SmoothTransformation)
            ox = r.x() + (r.width() - scaled.width()) // 2
            oy = r.y() + (r.height() - scaled.height()) // 2
            p.drawPixmap(ox, oy, scaled)
        else:
            if self._path:
                ext = Path(self._path).suffix.upper().lstrip(".")[:4]
                p.setPen(QColor(C['text2']))
                p.setFont(QFont(FONT_FAMILY, 9))
                p.drawText(r, Qt.AlignmentFlag.AlignCenter, ext or "?")
        p.end()

# ─── File viewers ─────────────────────────────────────────────────────────────

class ImageViewer(QWidget):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path = path
        self._scale = 1.0
        self._pan_start = None
        self._pan_offset = QPoint(0, 0)
        self._pixmap = QPixmap(str(path))
        self.setStyleSheet(f"background: {C['panel']};")
        self.setMouseTracking(True)
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        if self._pixmap.isNull():
            p.setPen(QColor(C['text2']))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Cannot load image")
            return
        w = int(self._pixmap.width() * self._scale)
        h = int(self._pixmap.height() * self._scale)
        # Fit initially
        if self._scale == 1.0:
            pw, ph = self._pixmap.width(), self._pixmap.height()
            sw, sh = self.width(), self.height()
            ratio = min(sw / max(pw, 1), sh / max(ph, 1))
            w, h = int(pw * ratio), int(ph * ratio)
            x = (sw - w) // 2 + self._pan_offset.x()
            y = (sh - h) // 2 + self._pan_offset.y()
        else:
            x = (self.width() - w) // 2 + self._pan_offset.x()
            y = (self.height() - h) // 2 + self._pan_offset.y()
        p.drawPixmap(x, y, w, h, self._pixmap)

    def wheelEvent(self, e):
        delta = e.angleDelta().y()
        factor = 1.15 if delta > 0 else 0.87
        self._scale = max(0.1, min(10.0, self._scale * factor))
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._pan_start = e.pos()
            self.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            e.accept()

    def mouseMoveEvent(self, e):
        if self._pan_start is not None:
            delta = e.pos() - self._pan_start
            self._pan_start = e.pos()
            self._pan_offset += delta
            self.update()

    def mouseReleaseEvent(self, e):
        self._pan_start = None
        self.setCursor(QCursor(Qt.CursorShape.OpenHandCursor))


class VideoViewer(QWidget):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path = path
        self._main_lay = QVBoxLayout(self)
        self._main_lay.setContentsMargins(0, 0, 0, 0)
        self._main_lay.setSpacing(4)
        self.setStyleSheet("background: #000;")

        if not HAS_MULTIMEDIA:
            lbl = QLabel("Multimedia not available.\nInstall PyQt6-Qt6Multimedia.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{C['text2']}; background:{C['panel']};")
            self._main_lay.addWidget(lbl)
            return

        # ── Create output objects (must outlive player) ────────────────────
        self._audio = QAudioOutput()
        self._audio.setVolume(0.8)
        self._video = QVideoWidget()
        self._video.setStyleSheet("background: #000;")

        # ── Player ────────────────────────────────────────────────────────
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)
        self._player.setVideoOutput(self._video)

        # ── Controls bar ──────────────────────────────────────────────────
        controls = QWidget()
        controls.setStyleSheet(f"background: {C['panel']};")
        ctrl_lay = QHBoxLayout(controls)
        ctrl_lay.setContentsMargins(8, 4, 8, 4)
        ctrl_lay.setSpacing(8)

        self._play_btn = QPushButton("▶")
        self._play_btn.setFixedSize(32, 32)
        self._play_btn.setStyleSheet(f"""
            QPushButton {{ background:{C['accent']}; color:{C['text']};
                border-radius:16px; font-size:14px; border:none; }}
        """)
        self._play_btn.clicked.connect(self._toggle_play)

        self._seek = QSlider(Qt.Orientation.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderMoved.connect(self._seek_to)

        self._time_lbl = QLabel("0:00 / 0:00")
        self._time_lbl.setStyleSheet(f"color:{C['text2']}; font-size:11px;")
        self._time_lbl.setFixedWidth(90)

        self._vol = QSlider(Qt.Orientation.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(80)
        self._vol.setFixedWidth(80)
        self._vol.valueChanged.connect(lambda v: self._audio.setVolume(v / 100))

        ctrl_lay.addWidget(self._play_btn)
        ctrl_lay.addWidget(self._seek, 1)
        ctrl_lay.addWidget(self._time_lbl)
        ctrl_lay.addWidget(QLabel("🔊"))
        ctrl_lay.addWidget(self._vol)

        self._video_container = QWidget()
        self._video_container.setStyleSheet("background:#000;")
        vc_lay = QVBoxLayout(self._video_container)
        vc_lay.setContentsMargins(0, 0, 0, 0)
        vc_lay.addWidget(self._video)

        self._main_lay.addWidget(self._video_container, 1)
        self._main_lay.addWidget(controls)

        self._player.positionChanged.connect(self._on_pos)
        self._player.durationChanged.connect(self._on_dur)
        self._player.playbackStateChanged.connect(self._on_state)

        # Load via reset_player — handles signal wiring + setSource
        self._reset_player(path)

    # ── Full player reset — call this every time path changes ──────────────
    def _reset_player(self, path: Path):
        """Fully reset the player state before loading any new source."""
        # 1. Disconnect all player signals (suppress errors if not connected)
        for sig in (self._player.mediaStatusChanged,
                    self._player.errorOccurred):
            try:
                sig.disconnect()
            except Exception:
                pass

        # 2. Stop + clear source + detach video output
        self._player.stop()
        self._player.setVideoOutput(None)
        self._player.setSource(QUrl())

        # 3. Flush pending Qt events so the old frame is cleared
        QApplication.processEvents()

        # 4. Re-attach outputs
        self._player.setVideoOutput(self._video)
        self._player.setAudioOutput(self._audio)

        # 5. Re-wire signals fresh
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)

        # 6. Set new source — play triggered only inside _on_media_status
        self._player.setSource(QUrl.fromLocalFile(str(path)))

    def _on_media_status(self, status):
        """Autoplay only once the media is truly loaded."""
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self._show_error_card("This file has an invalid or unreadable format.")
            return
        ready = (QMediaPlayer.MediaStatus.LoadedMedia,
                 QMediaPlayer.MediaStatus.BufferedMedia)
        if status in ready:
            self._player.play()

    def _on_error(self, error, error_string: str):
        """Handle codec/format errors with a friendly fallback card."""
        bad = (QMediaPlayer.Error.FormatError, QMediaPlayer.Error.ResourceError)
        if error in bad:
            self._show_error_card(error_string)

    def _show_error_card(self, detail: str = ""):
        """Replace the video area with a styled error card."""
        # Remove the video container widget and replace with the error card
        old = self._video_container
        card = self._make_error_card()
        self._main_lay.replaceWidget(old, card)
        old.hide()
        old.deleteLater()
        self._video_container = card

    def _make_error_card(self) -> QWidget:
        card = QWidget()
        card.setStyleSheet(f"background:{C['panel']}; border-radius:12px;")
        lay = QVBoxLayout(card)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay.setSpacing(12)

        icon = QLabel("🎬")
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon.setStyleSheet("font-size:52px; background:transparent;")
        lay.addWidget(icon)

        title = QLabel("This file can't be previewed")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"font-size:16px; font-weight:700; color:{C['text']}; background:transparent;")
        lay.addWidget(title)

        body = QLabel(
            "Your system is missing the codec needed to play this video.\n"
            "You can still sort or delete it using the buttons on the right."
        )
        body.setAlignment(Qt.AlignmentFlag.AlignCenter)
        body.setWordWrap(True)
        body.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(body)

        open_btn = QPushButton("Open in Default App")
        open_btn.setStyleSheet(f"""
            QPushButton {{background:{C['accent']}; color:#fff; border:none;
                border-radius:8px; padding:8px 20px; font-size:13px;}}
            QPushButton:hover {{background:#6fa8f8;}}
        """)
        open_btn.clicked.connect(
            lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._path))))
        lay.addWidget(open_btn, 0, Qt.AlignmentFlag.AlignCenter)

        return card

    def _toggle_play(self):
        if not HAS_MULTIMEDIA:
            return
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def toggle_play(self):
        self._toggle_play()

    def _seek_to(self, pos: int):
        if HAS_MULTIMEDIA:
            self._player.setPosition(pos)

    def _on_pos(self, pos: int):
        if not self._seek.isSliderDown():
            self._seek.setValue(pos)
        dur = self._player.duration()
        self._time_lbl.setText(f"{self._fmt_ms(pos)} / {self._fmt_ms(dur)}")

    def _on_dur(self, dur: int):
        self._seek.setRange(0, dur)

    def _on_state(self, state):
        playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self._play_btn.setText("⏸" if playing else "▶")

    def _fmt_ms(self, ms: int) -> str:
        s = ms // 1000
        return f"{s//60}:{s%60:02d}"

    def stop(self):
        if HAS_MULTIMEDIA:
            self._player.stop()

    def release(self):
        """Stop and fully release the file handle before move/delete."""
        if not HAS_MULTIMEDIA:
            return
        for sig in (self._player.mediaStatusChanged,
                    self._player.errorOccurred):
            try:
                sig.disconnect()
            except Exception:
                pass
        self._player.stop()
        self._player.setVideoOutput(None)
        self._player.setSource(QUrl())
        QApplication.processEvents()


class AudioViewer(QWidget):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self._path = path
        self.setStyleSheet(f"background: {C['panel']}; border-radius: 12px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 32, 32, 32)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Music note art
        icon_lbl = QLabel("♪")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet(f"font-size: 72px; color: {C['accent']}; background: transparent;")
        lay.addWidget(icon_lbl)

        name_lbl = QLabel(path.name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color: {C['text']}; background: transparent;")
        name_lbl.setWordWrap(True)
        lay.addWidget(name_lbl)

        if not HAS_MULTIMEDIA:
            lbl = QLabel("Multimedia not available.\nInstall PyQt6-Qt6Multimedia.")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{C['text2']}; background:transparent;")
            lay.addWidget(lbl)
            return

        # ── Create player and outputs ──────────────────────────────────────
        self._audio  = QAudioOutput()
        self._audio.setVolume(0.8)
        self._player = QMediaPlayer()
        self._player.setAudioOutput(self._audio)

        self._seek = QSlider(Qt.Orientation.Horizontal)
        self._seek.setRange(0, 0)
        self._seek.sliderMoved.connect(lambda v: self._player.setPosition(v))
        lay.addWidget(self._seek)

        ctrl_row = QWidget()
        ctrl_row.setStyleSheet("background: transparent;")
        ctrl_lay = QHBoxLayout(ctrl_row)
        ctrl_lay.setContentsMargins(0, 0, 0, 0)

        self._time_lbl = QLabel("0:00 / 0:00")
        self._time_lbl.setStyleSheet(f"color:{C['text2']}; font-size:11px; background:transparent;")

        self._play_btn = QPushButton("▶  Play")
        self._play_btn.setStyleSheet(f"""
            QPushButton {{ background:{C['accent']}; color:{C['text']};
                border-radius:8px; padding: 8px 24px; font-size:14px; font-weight:600; border:none; }}
        """)
        self._play_btn.clicked.connect(self._toggle_play)

        self._vol = QSlider(Qt.Orientation.Horizontal)
        self._vol.setRange(0, 100)
        self._vol.setValue(80)
        self._vol.setFixedWidth(90)
        self._vol.valueChanged.connect(lambda v: self._audio.setVolume(v / 100))

        ctrl_lay.addWidget(self._time_lbl)
        ctrl_lay.addStretch()
        ctrl_lay.addWidget(self._play_btn)
        ctrl_lay.addStretch()
        ctrl_lay.addWidget(QLabel("🔊"))
        ctrl_lay.addWidget(self._vol)
        lay.addWidget(ctrl_row)

        self._player.positionChanged.connect(self._on_pos)
        self._player.durationChanged.connect(lambda d: self._seek.setRange(0, d))
        self._player.playbackStateChanged.connect(self._on_state)

        # Load via reset — handles signal wiring + setSource
        self._reset_player(path)

    # ── Full player reset ─────────────────────────────────────────────────
    def _reset_player(self, path: Path):
        """Fully reset player state before loading a new source."""
        for sig in (self._player.mediaStatusChanged,
                    self._player.errorOccurred):
            try:
                sig.disconnect()
            except Exception:
                pass

        self._player.stop()
        self._player.setSource(QUrl())
        QApplication.processEvents()

        self._player.setAudioOutput(self._audio)
        self._player.mediaStatusChanged.connect(self._on_media_status)
        self._player.errorOccurred.connect(self._on_error)
        self._player.setSource(QUrl.fromLocalFile(str(path)))

    def _on_media_status(self, status):
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            return  # audio — just do nothing, leave controls visible
        ready = (QMediaPlayer.MediaStatus.LoadedMedia,
                 QMediaPlayer.MediaStatus.BufferedMedia)
        if status in ready:
            self._player.play()

    def _on_error(self, error, error_string: str):
        pass  # audio errors are non-fatal; controls remain usable

    def _toggle_play(self):
        if self._player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            self._player.pause()
        else:
            self._player.play()

    def toggle_play(self):
        if HAS_MULTIMEDIA:
            self._toggle_play()

    def _on_pos(self, pos):
        if not self._seek.isSliderDown():
            self._seek.setValue(pos)
        dur = self._player.duration()
        s = pos // 1000
        ds = dur // 1000
        self._time_lbl.setText(f"{s//60}:{s%60:02d} / {ds//60}:{ds%60:02d}")

    def _on_state(self, state):
        playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self._play_btn.setText("⏸  Pause" if playing else "▶  Play")

    def stop(self):
        if HAS_MULTIMEDIA:
            self._player.stop()

    def release(self):
        """Stop and fully release the file handle before move/delete."""
        if not HAS_MULTIMEDIA:
            return
        for sig in (self._player.mediaStatusChanged,
                    self._player.errorOccurred):
            try:
                sig.disconnect()
            except Exception:
                pass
        self._player.stop()
        self._player.setSource(QUrl())
        QApplication.processEvents()


class PDFViewer(QScrollArea):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setStyleSheet(f"background: {C['panel']}; border: none;")

        inner = QWidget()
        inner.setStyleSheet(f"background: {C['panel']};")
        lay = QVBoxLayout(inner)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(12)
        self.setWidget(inner)

        loaded = False
        if HAS_PYMUPDF:
            try:
                doc = fitz.open(str(path))
                zoom = 1.5
                mat = fitz.Matrix(zoom, zoom)
                for page_num in range(min(len(doc), 30)):
                    pg = doc[page_num]
                    pix = pg.get_pixmap(matrix=mat)
                    img = QImage(pix.samples, pix.width, pix.height,
                                 pix.stride, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)
                    lbl = QLabel()
                    lbl.setPixmap(pixmap)
                    lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    lbl.setStyleSheet("background: white; border-radius: 4px; padding: 4px;")
                    lay.addWidget(lbl)
                doc.close()
                loaded = True
            except Exception as ex:
                pass

        if not loaded and HAS_PYPDF:
            try:
                reader = PdfReader(str(path))
                text = "\n\n".join(
                    page.extract_text() or "" for page in reader.pages[:10]
                )
                te = QTextEdit()
                te.setReadOnly(True)
                te.setPlainText(text)
                lay.addWidget(te)
                loaded = True
            except Exception:
                pass

        if not loaded:
            lbl = QLabel("Cannot render PDF.\nInstall pymupdf: pip install pymupdf")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet(f"color:{C['text2']};")
            lay.addWidget(lbl)


class TextViewer(QWidget):
    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        te = QTextEdit()
        te.setReadOnly(True)
        try:
            with open(path, encoding="utf-8", errors="replace") as f:
                content = f.read(500_000)
            te.setPlainText(content)
        except Exception as ex:
            te.setPlainText(f"Error reading file:\n{ex}")
        lay.addWidget(te)


class GenericViewer(QWidget):
    open_clicked = pyqtSignal()

    def __init__(self, path: Path, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C['panel']}; border-radius: 12px;")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(40, 40, 40, 40)
        lay.setSpacing(16)
        lay.setAlignment(Qt.AlignmentFlag.AlignCenter)

        ext_lbl = QLabel(path.suffix.upper().lstrip(".") or "FILE")
        ext_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ext_lbl.setStyleSheet(f"""
            font-size: 48px; font-weight: 700; color: {C['accent']};
            background: {C['panel2']}; border-radius: 16px;
            padding: 24px 32px;
        """)
        lay.addWidget(ext_lbl)

        name_lbl = QLabel(path.name)
        name_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_lbl.setWordWrap(True)
        name_lbl.setStyleSheet(f"font-size: 15px; font-weight: 600; color:{C['text']}; background:transparent;")
        lay.addWidget(name_lbl)

        meta = get_file_meta(path)
        info = QLabel(f"{fmt_size(meta['size'])}  ·  Modified {fmt_date(meta['modified'])}")
        info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(info)

        open_btn = QPushButton("Open in Default App")
        open_btn.setStyleSheet(f"""
            QPushButton {{ background:{C['accent']}; color:{C['text']};
                border-radius:8px; padding:10px 24px; font-size:13px; border:none; font-weight:600;}}
            QPushButton:hover {{ background:{C['accent']}; opacity:0.8; }}
        """)
        open_btn.clicked.connect(self.open_clicked)
        lay.addWidget(open_btn, 0, Qt.AlignmentFlag.AlignCenter)

# ─── Swipeable viewer container ───────────────────────────────────────────────

class SwipeableViewer(QWidget):
    swipe_left  = pyqtSignal()   # delete
    swipe_right = pyqtSignal()   # skip/keep

    THRESHOLD = 100

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C['panel']}; border-radius: 12px;")
        self._card: QWidget | None = None
        self._drag_start_x: float | None = None
        self._current_offset = 0
        self._dragging = False
        self._anim: QPropertyAnimation | None = None
        self.setMouseTracking(True)

    def set_viewer(self, widget: QWidget):
        if self._card and self._card is not widget:
            old = self._card
            old.hide()
            old.setParent(None)
            old.deleteLater()
        self._card = widget
        self._card.setParent(self)
        self._card.setGeometry(0, 0, self.width(), self.height())
        self._card.show()
        self._current_offset = 0
        self._dragging = False
        self.update()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if self._card:
            self._card.setGeometry(self._current_offset, 0, self.width(), self.height())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._drag_start_x = e.position().x()
            self._dragging = True
            e.accept()

    def mouseMoveEvent(self, e):
        if self._dragging and self._drag_start_x is not None and self._card:
            offset = int(e.position().x() - self._drag_start_x)
            self._current_offset = offset
            self._card.setGeometry(offset, 0, self.width(), self.height())
            self.update()
            e.accept()

    def mouseReleaseEvent(self, e):
        if self._dragging:
            self._dragging = False
            if abs(self._current_offset) >= self.THRESHOLD:
                direction = -1 if self._current_offset < 0 else 1
                self._animate_out(direction)
            else:
                self._snap_back()
            self._drag_start_x = None
            self.update()

    def _animate_out(self, direction: int):
        if not self._card:
            return
        target_x = direction * (self.width() + 50)
        self._anim = QPropertyAnimation(self._card, b"geometry")
        self._anim.setDuration(200)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(QRect(self._current_offset, 0, self.width(), self.height()))
        self._anim.setEndValue(QRect(target_x, 0, self.width(), self.height()))
        if direction < 0:
            self._anim.finished.connect(self.swipe_left.emit)
        else:
            self._anim.finished.connect(self.swipe_right.emit)
        self._anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)

    def _snap_back(self):
        if not self._card:
            return
        self._anim = QPropertyAnimation(self._card, b"geometry")
        self._anim.setDuration(320)
        self._anim.setEasingCurve(QEasingCurve.Type.OutElastic)
        self._anim.setStartValue(QRect(self._current_offset, 0, self.width(), self.height()))
        self._anim.setEndValue(QRect(0, 0, self.width(), self.height()))
        self._anim.start(QAbstractAnimation.DeletionPolicy.DeleteWhenStopped)
        self._current_offset = 0
        self.update()

    def animate_file_out(self, direction: int):
        """Called programmatically (keyboard shortcut)."""
        self._current_offset = 1 if direction > 0 else -1
        self._animate_out(direction)

    def paintEvent(self, e):
        super().paintEvent(e)
        if self._dragging and self._current_offset != 0:
            p = QPainter(self)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            alpha = min(160, int(abs(self._current_offset) / self.THRESHOLD * 160))
            color = QColor(224, 92, 92, alpha) if self._current_offset < 0 \
                    else QColor(76, 175, 125, alpha)
            p.fillRect(self.rect(), color)
            # Label
            p.setPen(QColor(255, 255, 255, alpha))
            p.setFont(QFont(FONT_FAMILY, 22, QFont.Weight.Bold))
            label = "DELETE" if self._current_offset < 0 else "KEEP"
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, label)
            p.end()

# ─── Setup screens ────────────────────────────────────────────────────────────

class _SetupPage(QWidget):
    """Base class for setup pages — full-screen centered card."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background: {C['bg']};")
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QWidget()
        self._card.setFixedWidth(560)
        self._card.setStyleSheet(f"""
            background: {C['panel']};
            border-radius: 16px;
            border: 1px solid {C['border']};
        """)
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(40)
        shadow.setOffset(0, 8)
        shadow.setColor(QColor(0, 0, 0, 100))
        self._card.setGraphicsEffect(shadow)

        self._card_lay = QVBoxLayout(self._card)
        self._card_lay.setContentsMargins(40, 40, 40, 40)
        self._card_lay.setSpacing(16)

        outer.addWidget(self._card, 0, Qt.AlignmentFlag.AlignCenter)

    def _title(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 22px; font-weight: 700; color: {C['text']}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl

    def _subtitle(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setStyleSheet(f"font-size: 13px; color: {C['text2']}; background: transparent;")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setWordWrap(True)
        return lbl

    def _accent_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['accent']}; color: {C['text']};
                border: none; border-radius: 10px;
                padding: 12px 28px; font-size: 14px; font-weight: 600;
            }}
            QPushButton:hover {{ background: #6aa3ff; }}
            QPushButton:pressed {{ background: #3a7ae0; }}
        """)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        return btn


class Step1Widget(_SetupPage):
    folder_chosen = pyqtSignal(Path)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folder: Path | None = None

        self._card_lay.addWidget(self._title("Which folder would you like to sort?"))
        self._card_lay.addSpacing(8)

        choose_btn = self._accent_btn("Choose Folder…")
        choose_btn.clicked.connect(self._pick_folder)
        self._card_lay.addWidget(choose_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self._info_lbl = QLabel("")
        self._info_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._info_lbl.setStyleSheet(f"color:{C['text2']}; font-size:12px; background:transparent;")
        self._info_lbl.setWordWrap(True)
        self._card_lay.addWidget(self._info_lbl)

        self._path_lbl = QLabel("")
        self._path_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._path_lbl.setStyleSheet(f"color:{C['text']}; font-size:13px; font-weight:500; background:transparent;")
        self._path_lbl.setWordWrap(True)
        self._card_lay.addWidget(self._path_lbl)

        self._next_btn = self._accent_btn("Next →")
        self._next_btn.setVisible(False)
        self._next_btn.clicked.connect(self._go_next)
        self._card_lay.addWidget(self._next_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def _pick_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder to Sort")
        if path:
            self._folder = Path(path)
            count = dir_file_count(self._folder)
            total = dir_total_size(self._folder)
            self._path_lbl.setText(str(self._folder))
            self._info_lbl.setText(f"{count} files  ·  {fmt_size(total)}")
            self._next_btn.setVisible(True)

    def _go_next(self):
        if self._folder:
            self.folder_chosen.emit(self._folder)


class Step2Widget(_SetupPage):
    mode_chosen = pyqtSignal(str, object)  # mode, keep_path (or None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._keep_path: Path | None = None

        self._card_lay.addWidget(self._title("Choose a sorting mode"))
        self._card_lay.addSpacing(8)

        cards_row = QWidget()
        cards_row.setStyleSheet("background: transparent;")
        cr_lay = QHBoxLayout(cards_row)
        cr_lay.setSpacing(16)

        self._sort_card  = self._mode_card(
            "Sort Mode",
            "Sort files into destination folders.\nSwipe left to delete, number keys to move.",
            C['accent'])
        self._swipe_card = self._mode_card(
            "Swipe-Only Mode",
            "Swipe left to delete, right to keep.\nNo destination folders.",
            C['keep'])

        self._sort_card.clicked.connect(lambda: self._select(MODE_SORT))
        self._swipe_card.clicked.connect(lambda: self._select(MODE_SWIPE))

        cr_lay.addWidget(self._sort_card)
        cr_lay.addWidget(self._swipe_card)
        self._card_lay.addWidget(cards_row)

        # Keep folder option (swipe-only)
        self._swipe_opts = QWidget()
        self._swipe_opts.setStyleSheet(f"background:{C['panel2']}; border-radius:10px;")
        self._swipe_opts.setVisible(False)
        so_lay = QVBoxLayout(self._swipe_opts)
        so_lay.setContentsMargins(16, 12, 16, 12)
        so_lay.setSpacing(8)

        so_lay.addWidget(QLabel("Where should kept files go?"))

        self._keep_in_place_btn = self._small_btn("Keep in place (don't move)")
        self._keep_in_folder_btn = self._small_btn("Move to a specific folder…")
        self._keep_lbl = QLabel("")
        self._keep_lbl.setStyleSheet(f"color:{C['text2']}; font-size:11px; background:transparent;")

        self._keep_in_place_btn.clicked.connect(lambda: self._set_keep(None, in_place=True))
        self._keep_in_folder_btn.clicked.connect(self._pick_keep_folder)

        so_lay.addWidget(self._keep_in_place_btn)
        so_lay.addWidget(self._keep_in_folder_btn)
        so_lay.addWidget(self._keep_lbl)
        self._card_lay.addWidget(self._swipe_opts)

        self._next_btn = self._accent_btn("Next →")
        self._next_btn.setVisible(False)
        self._next_btn.clicked.connect(self._go_next)
        self._card_lay.addWidget(self._next_btn, 0, Qt.AlignmentFlag.AlignCenter)

        self._mode: str = ""

    def _mode_card(self, title: str, desc: str, color: str) -> QPushButton:
        btn = QPushButton()
        btn.setFixedSize(220, 120)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {C['panel2']}; border: 2px solid {C['border']};
                border-radius: 12px; text-align: center; padding: 12px;
            }}
            QPushButton:hover {{ border-color: {color}; background: {C['hover']}; }}
            QPushButton:pressed {{ background: {C['pressed']}; }}
        """)
        btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        inner = QVBoxLayout(btn)
        inner.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t = QLabel(title)
        t.setStyleSheet(f"font-size:14px; font-weight:700; color:{color}; background:transparent; border:none;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d = QLabel(desc)
        d.setStyleSheet(f"font-size:11px; color:{C['text2']}; background:transparent; border:none;")
        d.setAlignment(Qt.AlignmentFlag.AlignCenter)
        d.setWordWrap(True)
        inner.addWidget(t)
        inner.addWidget(d)
        return btn

    def _small_btn(self, text: str) -> QPushButton:
        btn = QPushButton(text)
        btn.setStyleSheet(f"""
            QPushButton {{background:{C['hover']}; color:{C['text']};
                border:1px solid {C['border']}; border-radius:8px; padding:6px 12px;}}
            QPushButton:hover {{background:{C['panel2']};}}
        """)
        return btn

    def _select(self, mode: str):
        self._mode = mode
        self._swipe_opts.setVisible(mode == MODE_SWIPE)
        if mode == MODE_SORT:
            self._next_btn.setVisible(True)
        else:
            self._next_btn.setVisible(False)
            self._set_keep(None, in_place=True)

    def _pick_keep_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select Keep Folder")
        if path:
            self._keep_path = Path(path)
            self._keep_lbl.setText(f"→ {path}")
            self._next_btn.setVisible(True)

    def _set_keep(self, path: Path | None, in_place: bool = False):
        self._keep_path = path
        if in_place:
            self._keep_lbl.setText("Files will stay in their current location")
        self._next_btn.setVisible(True)

    def _go_next(self):
        self.mode_chosen.emit(self._mode, self._keep_path)


class Step3Widget(_SetupPage):
    order_chosen = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._card_lay.addWidget(self._title("Choose sort order"))
        self._card_lay.addWidget(self._subtitle("You can change this any time during sorting."))
        self._card_lay.addSpacing(8)

        for opt in SORT_OPTIONS:
            btn = QPushButton(opt)
            btn.setCheckable(True)
            btn.setStyleSheet(f"""
                QPushButton {{
                    background:{C['panel2']}; color:{C['text']};
                    border:1.5px solid {C['border']}; border-radius:10px;
                    padding:12px 20px; font-size:13px; text-align:left;
                }}
                QPushButton:hover {{ border-color:{C['accent']}; background:{C['hover']}; }}
                QPushButton:checked {{
                    background:{C['accent']}; border-color:{C['accent']}; color:#fff;
                }}
            """)
            btn.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
            btn.clicked.connect(lambda checked, o=opt, b=btn: self._select(o, b))
            self._card_lay.addWidget(btn)
            if opt == SORT_ALPHA:
                btn.setChecked(True)
                self._selected_order = opt
                self._selected_btn = btn

        self._card_lay.addSpacing(8)
        next_btn = self._accent_btn("Next →")
        next_btn.clicked.connect(lambda: self.order_chosen.emit(self._selected_order))
        self._card_lay.addWidget(next_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def _select(self, order: str, btn: QPushButton):
        if hasattr(self, '_selected_btn'):
            self._selected_btn.setChecked(False)
        btn.setChecked(True)
        self._selected_order = order
        self._selected_btn = btn


class Step3BWidget(_SetupPage):
    """Build destination folders (Sort Mode only)."""
    folders_ready = pyqtSignal(list)  # list of {name, path, shortcut}

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folders: list = []
        self._card.setFixedWidth(640)

        self._card_lay.addWidget(self._title("Build your destination folders"))
        self._card_lay.addWidget(self._subtitle(
            "Add folders where files will be sorted. Keyboard shortcuts are assigned automatically."))
        self._card_lay.addSpacing(8)

        self._list_widget = QWidget()
        self._list_widget.setStyleSheet("background: transparent;")
        self._list_lay = QVBoxLayout(self._list_widget)
        self._list_lay.setContentsMargins(0, 0, 0, 0)
        self._list_lay.setSpacing(6)

        scroll = QScrollArea()
        scroll.setWidget(self._list_widget)
        scroll.setWidgetResizable(True)
        scroll.setFixedHeight(260)
        scroll.setStyleSheet(f"background:{C['panel2']}; border-radius:10px; border:1px solid {C['border']};")
        self._card_lay.addWidget(scroll)

        add_btn = QPushButton("＋  Add Folder")
        add_btn.setStyleSheet(f"""
            QPushButton {{background:{C['panel2']}; color:{C['accent']};
                border:1.5px dashed {C['accent']}; border-radius:10px; padding:10px 20px;
                font-size:13px; font-weight:600;}}
            QPushButton:hover {{background:{C['hover']};}}
        """)
        add_btn.clicked.connect(self._add_folder)
        self._card_lay.addWidget(add_btn)

        self._card_lay.addSpacing(8)
        self._start_btn = self._accent_btn("Start Sorting →")
        self._start_btn.setEnabled(False)
        self._start_btn.clicked.connect(lambda: self.folders_ready.emit(self._folders))
        self._card_lay.addWidget(self._start_btn, 0, Qt.AlignmentFlag.AlignCenter)

    def _add_folder(self):
        if len(self._folders) >= len(SHORTCUT_KEYS):
            return
        dlg = _AddFolderDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            name, path = dlg.result_name, dlg.result_path
            idx = len(self._folders)
            shortcut = SHORTCUT_KEYS[idx]
            self._folders.append({"name": name, "path": str(path) if path else "", "shortcut": shortcut})
            self._rebuild_list()
            self._start_btn.setEnabled(True)

    def _rebuild_list(self):
        while self._list_lay.count():
            item = self._list_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for i, folder in enumerate(self._folders):
            row = QWidget()
            row.setFixedHeight(44)
            row.setStyleSheet(f"background:{C['panel']}; border-radius:8px;")
            rl = QHBoxLayout(row)
            rl.setContentsMargins(10, 0, 10, 0)

            badge = QLabel(folder["shortcut"])
            badge.setFixedSize(24, 24)
            badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
            badge.setStyleSheet(f"""
                background:{C['accent']}; color:#fff; border-radius:5px;
                font-size:11px; font-weight:700;
            """)

            name_lbl = QLabel(folder["name"])
            name_lbl.setStyleSheet(f"color:{C['text']}; font-size:13px;")

            path_lbl = QLabel(folder["path"])
            path_lbl.setStyleSheet(f"color:{C['text2']}; font-size:11px;")
            path_lbl.setMaximumWidth(200)

            rm_btn = QPushButton("✕")
            rm_btn.setFixedSize(24, 24)
            rm_btn.setStyleSheet(f"""
                QPushButton {{background:{C['del']}; color:#fff; border:none;
                    border-radius:12px; font-size:11px;}}
                QPushButton:hover {{background:#ff7070;}}
            """)
            rm_btn.clicked.connect(lambda _, idx=i: self._remove(idx))

            rl.addWidget(badge)
            rl.addWidget(name_lbl)
            rl.addWidget(path_lbl, 1)
            rl.addWidget(rm_btn)
            self._list_lay.addWidget(row)

        self._list_lay.addStretch()

    def _remove(self, idx: int):
        self._folders.pop(idx)
        # Reassign shortcuts
        for i, f in enumerate(self._folders):
            f["shortcut"] = SHORTCUT_KEYS[i]
        self._rebuild_list()
        self._start_btn.setEnabled(bool(self._folders))


class _AddFolderDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Destination Folder")
        self.setModal(True)
        self.setFixedSize(440, 230)
        # Explicit color overrides so text is always white on the dark background
        dialog_qss = (GLOBAL_QSS +
                      f"QDialog{{background:{C['panel']};border-radius:12px;}}"
                      f"QDialog QLineEdit{{color:#ffffff;background:{C['panel2']};"
                      f"border:1.5px solid {C['border']};border-radius:6px;"
                      f"padding:2px 8px;height:28px;max-height:28px;min-height:28px;"
                      f"font-size:13px;}}"
                      f"QDialog QLineEdit:focus{{border-color:{C['accent']};}}"
                      f"QLabel{{color:{C['text']};background:transparent;}}")
        self.setStyleSheet(dialog_qss)
        self.result_name = ""
        self.result_path: Path | None = None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        lay.addWidget(QLabel("Folder name:"))
        self._name_edit = QLineEdit()
        self._name_edit.setPlaceholderText("e.g. Videos, Screenshots, Work…")
        self._name_edit.setFixedHeight(28)
        self._name_edit.setMaximumHeight(28)
        self._name_edit.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        lay.addWidget(self._name_edit)

        self._path_lbl = QLabel("Path: (will create subfolder in source folder)")
        self._path_lbl.setStyleSheet(f"color:{C['text2']}; font-size:11px;")
        lay.addWidget(self._path_lbl)

        row = QWidget()
        row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(row)
        rl.setContentsMargins(0, 0, 0, 0)
        self._browse_btn = QPushButton("Browse…")
        self._browse_btn.clicked.connect(self._browse)
        rl.addWidget(self._browse_btn)
        rl.addStretch()
        lay.addWidget(row)

        btns = QWidget()
        btns.setStyleSheet("background:transparent;")
        bl = QHBoxLayout(btns)
        bl.setContentsMargins(0, 0, 0, 0)
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        ok = QPushButton("Add")
        ok.setStyleSheet(f"""
            QPushButton {{background:{C['accent']};color:#fff;border:none;border-radius:8px;padding:8px 20px;}}
        """)
        ok.clicked.connect(self._accept)
        bl.addStretch()
        bl.addWidget(cancel)
        bl.addWidget(ok)
        lay.addWidget(btns)

        self._chosen_path: Path | None = None

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Select Existing Folder")
        if path:
            self._chosen_path = Path(path)
            self._path_lbl.setText(f"Path: {path}")
            if not self._name_edit.text():
                self._name_edit.setText(Path(path).name)

    def _accept(self):
        name = self._name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Name required", "Please enter a folder name.")
            return
        self.result_name = name
        self.result_path = self._chosen_path  # None = create subfolder later
        self.accept()

# ─── Sorting screen ───────────────────────────────────────────────────────────

class SortingScreen(QWidget):
    go_setup = pyqtSignal()

    def __init__(self, config: dict, parent=None):
        super().__init__(parent)
        self._config = config
        self._folder     = Path(config["folder"])
        self._mode       = config.get("mode", MODE_SORT)
        self._sort_order = config.get("sort_order", SORT_ALPHA)
        self._destinations: list = config.get("destinations", [])
        self._keep_path  = Path(config["keep_path"]) if config.get("keep_path") else None
        self._files: list[Path] = []
        self._current_idx: int  = config.get("current_index", 0)
        self._deleted_size: int = 0
        self._undo_stack: list  = []   # [{action, src, dst, idx, size}]
        self._current_viewer    = None
        self._folder_btns: list = []

        self._build_ui()
        self._load_files()
        self._build_folder_buttons()
        self._show_file(self._current_idx)
        self._setup_shortcuts()

    # ── UI construction ──────────────────────────────────────────────────────

    def _build_ui(self):
        self.setStyleSheet(f"background:{C['bg']};")
        main_lay = QVBoxLayout(self)
        main_lay.setContentsMargins(0, 0, 0, 0)
        main_lay.setSpacing(0)

        # ── Top bar ──────────────────────────────────────────────────────────
        top = QWidget()
        top.setFixedHeight(52)
        top.setStyleSheet(f"background:{C['panel']}; border-bottom:1px solid {C['border']};")
        tl = QHBoxLayout(top)
        tl.setContentsMargins(16, 0, 16, 0)
        tl.setSpacing(12)

        back_btn = QPushButton("← Back")
        back_btn.setStyleSheet(f"background:transparent; border:none; color:{C['text2']}; font-size:13px;")
        back_btn.clicked.connect(self._go_back)
        tl.addWidget(back_btn)

        self._folder_name_lbl = QLabel(self._folder.name)
        self._folder_name_lbl.setStyleSheet(f"font-size:14px; font-weight:600; color:{C['text']}; background:transparent;")
        tl.addWidget(self._folder_name_lbl)

        tl.addStretch()

        self._sort_combo = QComboBox()
        for opt in SORT_OPTIONS:
            self._sort_combo.addItem(opt)
        self._sort_combo.setCurrentText(self._sort_order)
        self._sort_combo.currentTextChanged.connect(self._change_sort)
        self._sort_combo.setFixedWidth(160)
        tl.addWidget(self._sort_combo)

        new_folder_btn = QPushButton("Sort New Folder")
        new_folder_btn.clicked.connect(self.go_setup.emit)
        tl.addWidget(new_folder_btn)

        disk_btn = QPushButton("Disk Analyzer")
        disk_btn.clicked.connect(self._open_disk_analyzer)
        tl.addWidget(disk_btn)

        main_lay.addWidget(top)

        # ── Progress bar ─────────────────────────────────────────────────────
        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setStyleSheet(f"""
            QProgressBar {{ background:{C['panel2']}; border:none; }}
            QProgressBar::chunk {{ background:{C['accent']}; }}
        """)
        main_lay.addWidget(self._progress)

        # ── Counter row ──────────────────────────────────────────────────────
        counter_row = QWidget()
        counter_row.setFixedHeight(28)
        counter_row.setStyleSheet(f"background:{C['bg']};")
        cl = QHBoxLayout(counter_row)
        cl.setContentsMargins(16, 0, 16, 0)

        self._counter_lbl = QLabel("0 / 0")
        self._counter_lbl.setStyleSheet(f"color:{C['text2']}; font-size:12px; background:transparent;")

        self._deleted_lbl = QLabel("🗑 0 B deleted")
        self._deleted_lbl.setStyleSheet(f"color:{C['del']}; font-size:12px; background:transparent;")

        cl.addWidget(self._counter_lbl)
        cl.addStretch()
        cl.addWidget(self._deleted_lbl)
        main_lay.addWidget(counter_row)

        # ── Main area (splitter) ─────────────────────────────────────────────
        self._splitter = QSplitter(Qt.Orientation.Horizontal)
        self._splitter.setStyleSheet(f"background:{C['bg']};")
        self._splitter.setHandleWidth(1)

        # Left: file viewer (65%)
        self._viewer_container = SwipeableViewer()
        self._viewer_container.swipe_left.connect(self._action_delete)
        self._viewer_container.swipe_right.connect(self._action_skip)
        self._splitter.addWidget(self._viewer_container)

        # Right: info + controls
        right_outer = QScrollArea()
        right_outer.setWidgetResizable(True)
        right_outer.setFrameShape(QFrame.Shape.NoFrame)
        right_outer.setStyleSheet(f"background:{C['panel']}; border-left:1px solid {C['border']};")

        self._right_widget = QWidget()
        self._right_widget.setStyleSheet(f"background:{C['panel']};")
        self._right_lay = QVBoxLayout(self._right_widget)
        self._right_lay.setContentsMargins(16, 16, 16, 16)
        self._right_lay.setSpacing(12)

        right_outer.setWidget(self._right_widget)
        self._splitter.addWidget(right_outer)
        self._splitter.setSizes([650, 350])

        main_lay.addWidget(self._splitter, 1)

        # ── Thumbnail strip ──────────────────────────────────────────────────
        self._thumb_strip = ThumbnailStrip()
        self._thumb_strip.jumped.connect(self._jump_to)
        main_lay.addWidget(self._thumb_strip)

        # Toast
        self._toast = Toast(self)

        # Build right panel static structure
        self._build_right_panel()

    def _build_right_panel(self):
        lay = self._right_lay

        # File info section
        self._fname_lbl = QLabel("")
        self._fname_lbl.setStyleSheet(f"font-size:16px; font-weight:700; color:{C['text']}; background:transparent;")
        self._fname_lbl.setWordWrap(True)
        lay.addWidget(self._fname_lbl)

        self._type_size_lbl = QLabel("")
        self._type_size_lbl.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(self._type_size_lbl)

        self._modified_lbl = QLabel("")
        self._modified_lbl.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(self._modified_lbl)

        self._created_lbl = QLabel("")
        self._created_lbl.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(self._created_lbl)

        self._extra_lbl = QLabel("")
        self._extra_lbl.setStyleSheet(f"font-size:12px; color:{C['text2']}; background:transparent;")
        lay.addWidget(self._extra_lbl)

        self._path_lbl = QLabel("")
        self._path_lbl.setStyleSheet(f"font-size:10px; color:{C['text2']}; background:transparent;")
        self._path_lbl.setWordWrap(True)
        lay.addWidget(self._path_lbl)

        # Rename row
        rename_row = QWidget()
        rename_row.setStyleSheet("background:transparent;")
        rl = QHBoxLayout(rename_row)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)
        self._rename_edit = QLineEdit()
        self._rename_edit.setPlaceholderText("Rename…")
        self._rename_edit.setVisible(False)
        self._rename_edit.returnPressed.connect(self._do_rename)
        self._rename_btn = QPushButton("Rename")
        self._rename_btn.setStyleSheet(f"""
            QPushButton {{background:transparent; color:{C['accent']};
                border:1px solid {C['accent']}; border-radius:6px; padding:4px 10px; font-size:11px;}}
            QPushButton:hover {{background:{C['accent']}; color:#fff;}}
        """)
        self._rename_btn.clicked.connect(self._toggle_rename)
        rl.addWidget(self._rename_edit, 1)
        rl.addWidget(self._rename_btn)
        lay.addWidget(rename_row)

        # Open file location
        show_btn = QPushButton("Open File Location")
        show_btn.setStyleSheet(f"""
            QPushButton {{background:transparent; color:{C['text2']};
                border:none; font-size:11px; text-align:left; padding:0;}}
            QPushButton:hover {{color:{C['text']};}}
        """)
        show_btn.clicked.connect(self._show_in_explorer)
        lay.addWidget(show_btn)

        # Divider
        lay.addWidget(self._divider())

        # Folder buttons area (Sort Mode)
        if self._mode == MODE_SORT:
            lay.addWidget(QLabel("Sort to folder:"))
            self._folders_widget = QWidget()
            self._folders_widget.setStyleSheet("background:transparent;")
            self._folders_lay = QVBoxLayout(self._folders_widget)
            self._folders_lay.setContentsMargins(0, 0, 0, 0)
            self._folders_lay.setSpacing(6)
            lay.addWidget(self._folders_widget)

            add_dest_btn = QPushButton("＋ Add Folder")
            add_dest_btn.setStyleSheet(f"""
                QPushButton {{background:transparent; color:{C['accent']};
                    border:1px dashed {C['accent']}; border-radius:8px; padding:6px 12px; font-size:11px;}}
                QPushButton:hover {{background:{C['hover']};}}
            """)
            add_dest_btn.clicked.connect(self._add_dest_folder)
            lay.addWidget(add_dest_btn)

            lay.addWidget(self._divider())

        # Action buttons
        action_row = QWidget()
        action_row.setStyleSheet("background:transparent;")
        al = QHBoxLayout(action_row)
        al.setContentsMargins(0, 0, 0, 0)
        al.setSpacing(8)

        self._delete_btn = QPushButton("🗑  Delete")
        self._delete_btn.setStyleSheet(f"""
            QPushButton {{background:{C['del']}; color:#fff; border:none;
                border-radius:8px; padding:10px 18px; font-size:13px; font-weight:600;}}
            QPushButton:hover {{background:#f07070;}}
            QPushButton:pressed {{background:#c04040;}}
        """)
        self._delete_btn.clicked.connect(self._action_delete)

        self._skip_btn = QPushButton("Skip  →")
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{background:{C['panel2']}; color:{C['text']}; border:1px solid {C['border']};
                border-radius:8px; padding:10px 18px; font-size:13px; font-weight:600;}}
            QPushButton:hover {{background:{C['hover']};}}
        """)
        self._skip_btn.clicked.connect(self._action_skip)

        al.addWidget(self._delete_btn, 1)
        al.addWidget(self._skip_btn, 1)
        lay.addWidget(action_row)
        lay.addStretch()

    def _divider(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setStyleSheet(f"background:{C['border']}; border:none; max-height:1px;")
        return f

    # ── File loading ─────────────────────────────────────────────────────────

    def _load_files(self):
        try:
            all_files = [p for p in self._folder.iterdir()
                         if p.is_file() and p.name != CONFIG_FILENAME
                         and not p.name.startswith("._sorter")]
        except Exception:
            all_files = []

        order = self._sort_order
        if order == SORT_ALPHA:
            all_files.sort(key=lambda p: p.name.lower())
        elif order == SORT_TYPE:
            all_files.sort(key=lambda p: (p.suffix.lower(), p.name.lower()))
        elif order == SORT_SIZE:
            all_files.sort(key=lambda p: p.stat().st_size if p.exists() else 0, reverse=True)
        elif order == SORT_DATE:
            all_files.sort(key=lambda p: p.stat().st_mtime if p.exists() else 0, reverse=True)

        self._files = all_files
        self._current_idx = min(self._current_idx, max(0, len(self._files) - 1))
        self._update_progress()
        self._thumb_strip.set_files(self._files, self._current_idx)

    def _build_folder_buttons(self):
        if self._mode != MODE_SORT:
            return
        while self._folders_lay.count():
            item = self._folders_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._folder_btns = []
        for dest in self._destinations:
            btn = FolderPillBtn(dest["name"], dest.get("shortcut", "?"))
            btn.clicked.connect(lambda _, d=dest: self._action_move(d))
            self._folders_lay.addWidget(btn)
            self._folder_btns.append(btn)

    # ── File display ─────────────────────────────────────────────────────────

    def _show_file(self, idx: int):
        if not self._files:
            self._show_done()
            return
        if idx < 0 or idx >= len(self._files):
            self._show_done()
            return

        # Stop any active media
        if self._current_viewer and hasattr(self._current_viewer, "stop"):
            self._current_viewer.stop()

        self._current_idx = idx
        path = self._files[idx]
        ext  = path.suffix.lower()

        # Create viewer
        if ext in IMAGE_EXTS:
            viewer = ImageViewer(path)
        elif ext in VIDEO_EXTS and HAS_MULTIMEDIA:
            viewer = VideoViewer(path)
        elif ext in AUDIO_EXTS:
            viewer = AudioViewer(path)
        elif ext in PDF_EXTS:
            viewer = PDFViewer(path)
        elif ext in TEXT_EXTS:
            viewer = TextViewer(path)
        else:
            viewer = GenericViewer(path)
            viewer.open_clicked.connect(lambda p=path: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p))))

        self._current_viewer = viewer
        self._viewer_container.set_viewer(viewer)

        # Update info panel
        self._update_info_panel(path)
        self._update_progress()
        self._thumb_strip.update_current(idx)
        self._save_session()

    def _update_info_panel(self, path: Path):
        meta = get_file_meta(path)
        self._fname_lbl.setText(path.name)
        self._type_size_lbl.setText(f"{file_type_label(path)}  ·  {fmt_size(meta['size'])}")
        self._modified_lbl.setText(f"Modified: {fmt_date(meta['modified'])}")
        self._created_lbl.setText(f"Created: {fmt_date(meta['created'])}")
        self._path_lbl.setText(f"Path: {path}")
        self._rename_edit.setText(path.stem)
        self._rename_edit.setVisible(False)

        # Extra info
        ext = path.suffix.lower()
        extra = ""
        if ext in IMAGE_EXTS:
            try:
                img = QImage(str(path))
                if not img.isNull():
                    extra = f"Dimensions: {img.width()} × {img.height()}"
            except Exception:
                pass
        self._extra_lbl.setText(extra)

    def _update_progress(self):
        total = len(self._files)
        cur   = self._current_idx + 1
        self._counter_lbl.setText(f"{cur} / {total}")
        self._progress.setMaximum(max(total, 1))
        self._progress.setValue(self._current_idx)
        self._deleted_lbl.setText(f"🗑 {fmt_size(self._deleted_size)} deleted")

    def _show_done(self):
        done = QWidget()
        done.setStyleSheet(f"background:{C['panel']}; border-radius:12px;")
        dl = QVBoxLayout(done)
        dl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dl.setSpacing(16)
        t = QLabel("All done! 🎉")
        t.setStyleSheet(f"font-size:28px; font-weight:700; color:{C['text']}; background:transparent;")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s = QLabel(f"You sorted {len(self._files)} files\n{fmt_size(self._deleted_size)} deleted")
        s.setStyleSheet(f"font-size:14px; color:{C['text2']}; background:transparent;")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        dl.addWidget(t)
        dl.addWidget(s)
        btn = QPushButton("Sort a New Folder")
        btn.setStyleSheet(f"""
            QPushButton {{background:{C['accent']};color:#fff;border:none;
                border-radius:10px;padding:12px 28px;font-size:14px;font-weight:600;}}
        """)
        btn.clicked.connect(self.go_setup.emit)
        dl.addWidget(btn, 0, Qt.AlignmentFlag.AlignCenter)
        self._viewer_container.set_viewer(done)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _action_delete(self):
        if not self._files or self._current_idx >= len(self._files):
            return
        path = self._files[self._current_idx]
        if not path.exists():
            self._advance()
            return
        try:
            size = path.stat().st_size
        except Exception:
            size = 0

        # Release media handle BEFORE deleting (fixes WinError 32 file lock)
        if self._current_viewer and hasattr(self._current_viewer, "release"):
            self._current_viewer.release()

        # Send directly to OS Recycle Bin / Trash
        try:
            if HAS_SEND2TRASH:
                send2trash.send2trash(str(path))
            else:
                path.unlink(missing_ok=True)
        except Exception as ex:
            self._toast.show_message(f"Error: {ex}")
            return

        self._deleted_size += size
        self._undo_stack = [{
            "action": "delete",
            "idx": self._current_idx,
            "size": size,
        }]
        self._toast.show_message("Sent to Recycle Bin")
        self._viewer_container.animate_file_out(-1)
        QTimer.singleShot(210, self._advance_after_animate)

    def _action_skip(self):
        if not self._files:
            return
        self._undo_stack = [{"action": "skip", "idx": self._current_idx}]
        self._toast.show_message(f"Skipped  ·  {self._undo_hint()}")
        self._viewer_container.animate_file_out(1)
        QTimer.singleShot(210, self._advance_after_animate)

    def _action_move(self, dest: dict):
        if not self._files or self._current_idx >= len(self._files):
            return
        path = self._files[self._current_idx]
        if not path.exists():
            self._advance()
            return

        # Release any media handle before moving
        if self._current_viewer and hasattr(self._current_viewer, "release"):
            self._current_viewer.release()

        # Resolve destination folder
        dst_folder = Path(dest["path"])
        if not dst_folder.is_absolute():
            dst_folder = self._folder / dst_folder
        if dst_folder == self._folder or not dest["path"]:
            # Create subfolder
            dst_folder = self._folder / dest["name"]

        try:
            moved_to = safe_move(path, dst_folder)
        except Exception as ex:
            self._toast.show_message(f"Error moving: {ex}")
            return

        self._undo_stack = [{
            "action": "move",
            "src": str(path),
            "dst": str(moved_to),
            "idx": self._current_idx,
            "size": 0,
        }]
        self._toast.show_message(f"Moved to {dest['name']}  ·  {self._undo_hint()}")
        self._viewer_container.animate_file_out(1)
        QTimer.singleShot(210, self._advance_after_animate)

    def _action_undo(self):
        if not self._undo_stack:
            self._toast.show_message("Nothing to undo")
            return
        entry = self._undo_stack.pop()
        action = entry["action"]

        if action == "move":
            src, dst = Path(entry["src"]), Path(entry["dst"])
            try:
                if dst.exists():
                    shutil.move(str(dst), str(src))
                self._current_idx = entry["idx"]
                self._load_files()
                self._show_file(self._current_idx)
                self._toast.show_message("Undone: move reversed")
            except Exception as ex:
                self._toast.show_message(f"Undo failed: {ex}")

        elif action == "delete":
            self._toast.show_message("Deleted files are in the Recycle Bin — restore from there")

        elif action == "skip":
            self._current_idx = entry["idx"]
            self._show_file(self._current_idx)
            self._toast.show_message("Undone: went back")

    def _undo_hint(self) -> str:
        return "⌘Z to undo" if IS_MAC else "Ctrl+Z to undo"

    def _advance(self):
        next_idx = self._current_idx + 1
        if next_idx >= len(self._files):
            self._show_done()
        else:
            self._show_file(next_idx)

    def _advance_after_animate(self):
        last = self._undo_stack[-1] if self._undo_stack else None
        consumed = last and last["action"] in ("delete", "move")

        if consumed:
            # File was removed from disk; drop it from our list
            if self._current_idx < len(self._files):
                self._files.pop(self._current_idx)
            # Stay at same index (now pointing to what was the next file)
            next_idx = min(self._current_idx, max(0, len(self._files) - 1))
        else:
            # Skip — just advance
            next_idx = self._current_idx + 1

        self._update_progress()

        if not self._files:
            self._show_done()
        elif next_idx >= len(self._files):
            self._show_done()
        else:
            self._show_file(next_idx)

    def _jump_to(self, idx: int):
        if 0 <= idx < len(self._files):
            self._show_file(idx)

    def _change_sort(self, order: str):
        self._sort_order = order
        self._load_files()
        self._show_file(0)

    def _add_dest_folder(self):
        dlg = _AddFolderDialog(self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            idx = len(self._destinations)
            if idx >= len(SHORTCUT_KEYS):
                return
            shortcut = SHORTCUT_KEYS[idx]
            self._destinations.append({
                "name": dlg.result_name,
                "path": str(dlg.result_path) if dlg.result_path else "",
                "shortcut": shortcut,
            })
            self._build_folder_buttons()
            self._setup_shortcuts()

    def _toggle_rename(self):
        visible = self._rename_edit.isVisible()
        self._rename_edit.setVisible(not visible)
        if not visible:
            self._rename_edit.setFocus()
            self._rename_btn.setText("Confirm")
        else:
            self._rename_btn.setText("Rename")

    def _do_rename(self):
        if not self._files or self._current_idx >= len(self._files):
            return
        path = self._files[self._current_idx]
        new_stem = self._rename_edit.text().strip()
        if not new_stem or new_stem == path.stem:
            self._rename_edit.setVisible(False)
            self._rename_btn.setText("Rename")
            return
        new_path = path.parent / (new_stem + path.suffix)
        new_path = collision_free(new_path)
        try:
            path.rename(new_path)
            self._files[self._current_idx] = new_path
            self._update_info_panel(new_path)
            self._toast.show_message(f"Renamed to {new_path.name}")
        except Exception as ex:
            self._toast.show_message(f"Rename failed: {ex}")
        self._rename_edit.setVisible(False)
        self._rename_btn.setText("Rename")

    def _show_in_explorer(self):
        if not self._files or self._current_idx >= len(self._files):
            return
        path = self._files[self._current_idx]
        try:
            if IS_MAC:
                subprocess.Popen(["open", "-R", str(path)])
            else:
                subprocess.Popen(["explorer", "/select,", os.path.normpath(str(path))])
        except Exception:
            pass

    def _go_back(self):
        self.go_setup.emit()

    def _open_disk_analyzer(self):
        dlg = DiskAnalyzerDialog(self._folder, self)
        dlg.view_requested.connect(self._view_from_disk_analyzer)
        dlg.exec()

    def _view_from_disk_analyzer(self, path_str: str, kind: str):
        """Open the sorter pointed at a file/folder from the Disk Analyzer."""
        target = Path(path_str)
        if kind == "file" and target.is_file():
            folder = target.parent
            # Switch the sorter to the file's parent folder, sorted by size desc,
            # and jump directly to the target file.
            try:
                files = sorted(
                    [p for p in folder.iterdir()
                     if p.is_file() and not p.name.startswith("._sorter")],
                    key=lambda p: p.stat().st_size if p.exists() else 0,
                    reverse=True,
                )
            except Exception:
                files = [target]
            idx = 0
            for i, f in enumerate(files):
                if f == target:
                    idx = i
                    break
            self._folder      = folder
            self._files       = files
            self._current_idx = idx
            self._update_progress()
            self._show_file(idx)
        elif kind == "dir" and target.is_dir():
            # For a directory, emit go_setup so the user can configure sorting for it
            self.go_setup.emit()

    def _save_session(self):
        state = {
            "folder":       str(self._folder),
            "mode":         self._mode,
            "sort_order":   self._sort_order,
            "destinations": self._destinations,
            "current_index": self._current_idx,
            "keep_path":    str(self._keep_path) if self._keep_path else None,
        }
        save_session(self._folder, state)

    # ── Keyboard shortcuts ────────────────────────────────────────────────────

    def _setup_shortcuts(self):
        mod = Qt.KeyboardModifier.ControlModifier if IS_WIN else Qt.KeyboardModifier.MetaModifier

        for sc in [
            (QKeySequence(Qt.Key.Key_Left),  self._action_delete),
            (QKeySequence(Qt.Key.Key_Right), self._action_skip),
            (QKeySequence(Qt.Key.Key_A),     self._go_prev),
            (QKeySequence(Qt.Key.Key_D),     self._action_skip),
            (QKeySequence(Qt.Key.Key_Space), self._toggle_play),
            (QKeySequence.StandardKey.Undo,  self._action_undo),
        ]:
            s = QShortcut(sc[0], self)
            s.activated.connect(sc[1])

        # Number + letter shortcuts for destinations
        for i, dest in enumerate(self._destinations):
            key_char = SHORTCUT_KEYS[i]
            key = getattr(Qt.Key, f"Key_{key_char}", None)
            if key:
                s = QShortcut(QKeySequence(key), self)
                s.activated.connect(lambda d=dest: self._action_move(d))

    def _go_prev(self):
        if self._current_idx > 0:
            self._show_file(self._current_idx - 1)

    def _toggle_play(self):
        if self._current_viewer and hasattr(self._current_viewer, "toggle_play"):
            self._current_viewer.toggle_play()

    def resizeEvent(self, e):
        super().resizeEvent(e)
        if hasattr(self, "_toast"):
            self._toast._reposition()

# ─── Disk Analyzer ────────────────────────────────────────────────────────────

class DiskAnalyzerDialog(QDialog):
    view_requested = pyqtSignal(str, str)  # path_str, kind ("file" | "dir")

    def __init__(self, default_folder: Path | None = None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Disk Analyzer")
        self.setMinimumSize(900, 600)
        self.setStyleSheet(GLOBAL_QSS + f"QDialog{{background:{C['bg']};border-radius:12px;}}")
        self._worker: DiskScanWorker | None = None
        self._all_files: list  = []   # accumulated file items
        self._all_dirs:  list  = []   # accumulated dir items
        self._default_folder = default_folder

        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 24, 24, 24)
        lay.setSpacing(12)

        # Header
        hdr = QHBoxLayout()
        title = QLabel("Disk Analyzer")
        title.setStyleSheet(f"font-size:20px; font-weight:700; color:{C['text']}; background:transparent;")
        hdr.addWidget(title)
        hdr.addStretch()
        browse_btn = QPushButton("Scan Folder…")
        browse_btn.clicked.connect(self._pick_scan_folder)
        hdr.addWidget(browse_btn)
        self._scan_btn = QPushButton("Scan Computer")
        self._scan_btn.clicked.connect(lambda: self._start_scan(None))
        hdr.addWidget(self._scan_btn)
        self._cancel_btn = QPushButton("Cancel")
        self._cancel_btn.setVisible(False)
        self._cancel_btn.clicked.connect(self._cancel_scan)
        hdr.addWidget(self._cancel_btn)
        lay.addLayout(hdr)

        status_row = QHBoxLayout()
        self._scan_path_lbl = QLabel("")
        self._scan_path_lbl.setStyleSheet(f"color:{C['text2']}; font-size:12px; background:transparent;")
        self._spinner_lbl = QLabel("⏳")
        self._spinner_lbl.setStyleSheet("font-size:14px; background:transparent;")
        self._spinner_lbl.setVisible(False)
        status_row.addWidget(self._spinner_lbl)
        status_row.addWidget(self._scan_path_lbl, 1)
        lay.addLayout(status_row)

        self._progress = QProgressBar()
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setRange(0, 0)   # indeterminate
        self._progress.setVisible(False)
        lay.addWidget(self._progress)

        # Spinner animation timer
        self._spin_chars = ["⏳", "🔄", "⌛", "🔄"]
        self._spin_idx = 0
        self._spin_timer = QTimer(self)
        self._spin_timer.timeout.connect(self._tick_spinner)

        # Tabs
        self._tabs = QTabWidget()
        self._table_files   = self._make_table()
        self._table_folders = self._make_table()
        self._tabs.addTab(self._table_files,   "Files")
        self._tabs.addTab(self._table_folders, "Folders")
        lay.addWidget(self._tabs, 1)

    def _make_table(self) -> QTableWidget:
        t = QTableWidget(0, 4)
        t.setHorizontalHeaderLabels(["Name", "Path", "Size", "Actions"])
        t.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        t.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        t.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        t.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        t.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        t.verticalHeader().setVisible(False)
        t.setShowGrid(False)
        t.setAlternatingRowColors(False)
        return t

    def _tick_spinner(self):
        self._spin_idx = (self._spin_idx + 1) % len(self._spin_chars)
        self._spinner_lbl.setText(self._spin_chars[self._spin_idx])

    def _pick_scan_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Select folder to scan")
        if path:
            self._start_scan(Path(path))

    def _start_scan(self, root: Path | None):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(300)

        self._all_files.clear()
        self._all_dirs.clear()
        self._table_files.setRowCount(0)
        self._table_folders.setRowCount(0)

        self._scan_path_lbl.setText(f"Scanning: {root or 'Entire computer'}…")
        self._progress.setVisible(True)
        self._spinner_lbl.setVisible(True)
        self._spin_timer.start(400)
        self._scan_btn.setEnabled(False)
        self._cancel_btn.setVisible(True)

        self._worker = DiskScanWorker(root)
        self._worker.batch_ready.connect(self._on_batch)
        self._worker.finished_scan.connect(self._on_finished)
        self._worker.start()

    def _cancel_scan(self):
        if self._worker and self._worker.isRunning():
            self._worker.abort()
        self._on_finished()

    def _on_batch(self, batch: list):
        """Receive 50 items at a time and stream into tables (top 200 each)."""
        needs_file_refresh = False
        needs_dir_refresh  = False

        for item in batch:
            if item["kind"] == "file":
                self._all_files.append(item)
                needs_file_refresh = True
            else:
                self._all_dirs.append(item)
                needs_dir_refresh = True

        if needs_file_refresh:
            # Keep only top 200 by size — re-sort and repopulate
            self._all_files.sort(key=lambda r: r["size"], reverse=True)
            top = self._all_files[:200]
            self._populate_table(self._table_files, top)

        if needs_dir_refresh:
            self._all_dirs.sort(key=lambda r: r["size"], reverse=True)
            top = self._all_dirs[:200]
            self._populate_table(self._table_folders, top)

        total = len(self._all_files) + len(self._all_dirs)
        self._scan_path_lbl.setText(f"Scanning… {total:,} items found so far")

    def _on_finished(self):
        self._progress.setVisible(False)
        self._spinner_lbl.setVisible(False)
        self._spin_timer.stop()
        self._scan_btn.setEnabled(True)
        self._cancel_btn.setVisible(False)
        total = len(self._all_files) + len(self._all_dirs)
        self._scan_path_lbl.setText(f"Scan complete — {total:,} items found")

    def _populate_table(self, table: QTableWidget, rows: list):
        table.setUpdatesEnabled(False)
        table.setRowCount(0)
        for row in rows:
            r = table.rowCount()
            table.insertRow(r)
            table.setItem(r, 0, QTableWidgetItem(row["name"]))
            table.setItem(r, 1, QTableWidgetItem(row["path"]))
            table.setItem(r, 2, QTableWidgetItem(fmt_size(row["size"])))

            # Action buttons
            cell = QWidget()
            cell.setStyleSheet("background:transparent;")
            cl = QHBoxLayout(cell)
            cl.setContentsMargins(4, 2, 4, 2)
            cl.setSpacing(4)

            view_btn = QPushButton("View")
            view_btn.setStyleSheet(f"""
                QPushButton {{background:{C['accent']}; color:#fff; border:none;
                    border-radius:5px; padding:3px 8px; font-size:11px;}}
                QPushButton:hover {{background:#6fa8f8;}}
            """)
            view_btn.clicked.connect(
                lambda _, p=row["path"], k=row["kind"]: self.view_requested.emit(p, k))

            del_btn = QPushButton("Delete")
            del_btn.setStyleSheet(f"""
                QPushButton {{background:{C['del']}; color:#fff; border:none;
                    border-radius:5px; padding:3px 8px; font-size:11px;}}
                QPushButton:hover {{background:#f07070;}}
            """)
            del_btn.clicked.connect(lambda _, p=row["path"]: self._delete_item(p))

            cl.addWidget(view_btn)
            cl.addWidget(del_btn)
            cl.addStretch()
            table.setCellWidget(r, 3, cell)
            table.setRowHeight(r, 38)
        table.setUpdatesEnabled(True)

    def _delete_item(self, path_str: str):
        path = Path(path_str)
        reply = QMessageBox.question(self, "Confirm delete",
            f"Send to trash?\n{path_str}",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            try:
                if HAS_SEND2TRASH:
                    send2trash.send2trash(path_str)
                else:
                    if path.is_file():
                        path.unlink()
                    elif path.is_dir():
                        shutil.rmtree(path_str)
            except Exception as ex:
                QMessageBox.warning(self, "Error", str(ex))

    def closeEvent(self, e):
        self._spin_timer.stop()
        if self._worker and self._worker.isRunning():
            self._worker.abort()
            self._worker.wait(500)
        super().closeEvent(e)

# ─── Main Window ──────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FileSorter")
        self.setMinimumSize(1100, 720)
        self.resize(1280, 800)
        self.setStyleSheet(GLOBAL_QSS)

        self._stack = QStackedWidget()
        self.setCentralWidget(self._stack)

        self._wizard = SetupWizard()
        self._wizard.start_sorting.connect(self._launch_sorter)
        self._stack.addWidget(self._wizard)

        self._sorting_screen: SortingScreen | None = None
        self._stack.setCurrentWidget(self._wizard)

    def _launch_sorter(self, config: dict):
        # Check for saved session
        folder = Path(config["folder"])
        saved  = load_session(folder)
        if saved and saved.get("current_index", 0) > 0:
            reply = QMessageBox.question(
                self, "Resume session?",
                f"Resume where you left off? (file {saved['current_index'] + 1})",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                config = saved

        if self._sorting_screen:
            self._stack.removeWidget(self._sorting_screen)
            self._sorting_screen.deleteLater()

        self._sorting_screen = SortingScreen(config)
        self._sorting_screen.go_setup.connect(self._back_to_setup)
        self._stack.addWidget(self._sorting_screen)
        self._stack.setCurrentWidget(self._sorting_screen)

    def _back_to_setup(self):
        self._wizard.reset_to_step1()
        self._stack.setCurrentWidget(self._wizard)


class SetupWizard(QWidget):
    start_sorting = pyqtSignal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"background:{C['bg']};")
        self._config: dict = {}

        self._stack = QStackedWidget()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)

        # Logo strip
        header = QWidget()
        header.setFixedHeight(56)
        header.setStyleSheet(f"background:{C['panel']}; border-bottom:1px solid {C['border']};")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(24, 0, 24, 0)
        logo = QLabel("FileSorter")
        logo.setStyleSheet(f"font-size:18px; font-weight:700; color:{C['accent']}; background:transparent;")
        hl.addWidget(logo)
        hl.addStretch()

        lay.addWidget(header)
        lay.addWidget(self._stack, 1)

        self._step1 = Step1Widget()
        self._step2 = Step2Widget()
        self._step3 = Step3Widget()
        self._step3b = Step3BWidget()
        for w in [self._step1, self._step2, self._step3, self._step3b]:
            self._stack.addWidget(w)

        self._step1.folder_chosen.connect(self._on_folder)
        self._step2.mode_chosen.connect(self._on_mode)
        self._step3.order_chosen.connect(self._on_order)
        self._step3b.folders_ready.connect(self._on_folders)

        self._stack.setCurrentWidget(self._step1)

    def _on_folder(self, folder: Path):
        self._config["folder"] = str(folder)
        self._stack.setCurrentWidget(self._step2)

    def _on_mode(self, mode: str, keep_path):
        self._config["mode"]      = mode
        self._config["keep_path"] = str(keep_path) if keep_path else None
        self._stack.setCurrentWidget(self._step3)

    def _on_order(self, order: str):
        self._config["sort_order"] = order
        if self._config.get("mode") == MODE_SORT:
            self._stack.setCurrentWidget(self._step3b)
        else:
            self._config["destinations"] = []
            self._config["current_index"] = 0
            self.start_sorting.emit(self._config)

    def _on_folders(self, folders: list):
        self._config["destinations"]  = folders
        self._config["current_index"] = 0
        self.start_sorting.emit(self._config)

    def reset_to_step1(self):
        """Reset wizard state and return to folder-picker step."""
        self._config = {}
        self._stack.setCurrentWidget(self._step1)

# ─── Entry point ──────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("FileSorter")
    app.setOrganizationName("FileSorter")
    app.setStyleSheet(GLOBAL_QSS)

    # High-DPI
    if hasattr(Qt.ApplicationAttribute, "AA_UseHighDpiPixmaps"):
        app.setAttribute(Qt.ApplicationAttribute.AA_UseHighDpiPixmaps, True)

    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
