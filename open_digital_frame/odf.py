# -*- coding: utf-8 -*-
"""
Open Digital Frame -- Directory browser for a digital frame

Browse a tree of directories containing images and playlist 
files. The directories are represented in a scrollable window, 
each with a thumbnail and a title. The thumbnail is taken from a 
folder.jpg file and some metadata are read from a folder.nfo 
file.

If a directory contains a playlist file (playlist_16x9.m3u, 
playlist.m3u, ...), selecting its thumbnail will start the 
slideshow using the photo-reframe companion program.
"""

from PyQt5.QtCore import (
    Qt,
    QSize,
    QEvent,
    QMutex,
    QObject,
    QRect,
    QThread,
    QTimer,
    pyqtSignal)
from PyQt5.QtGui import (
    QCursor,
    QPixmap,
    QFont,
    QFontMetrics)
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QLabel,
    QMainWindow,
    QScrollArea,
    QSpacerItem,
    QVBoxLayout,
    QWidget)
import xml.etree.ElementTree as ET

import configparser
import datetime
import importlib
import json
import logging
import math
import os
import os.path
import pathlib
import re
import subprocess
import sys
import time

__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2023 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.2.1"


# Some useful mappings from string to values.
map_logging = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL }

map_weight = {
    'Thin': QFont.Thin,
    'ExtraLight': QFont.ExtraLight,
    'Light': QFont.Light,
    'Normal': QFont.Normal,
    'Medium': QFont.Medium,
    'DemiBold': QFont.DemiBold,
    'Bold': QFont.Bold,
    'ExtraBold': QFont.ExtraBold,
    'Black': QFont.Black }

# Initialize defaults and read the configuration file.
CFG_FILE = 'open-digital-frame.ini'
if len(sys.argv) > 1:
    CFG_FILE = sys.argv[1]
cfg = configparser.ConfigParser()
cfg['DEFAULT'] = {
    'title': 'OpenDigitalFrame',
    'lbl_title_prefix': 'Digital Frame',
    'lbl_sort_by': 'Sort by',
    'lbl_reverse': 'rev.',
    'skin': 'skin_default',
    'pictures_root': '',
    'player_cmd': "photo-reframe --fullscreen --play --timer 5 --read-only {f}",
    'folder_thumbnails': '["folder.jpg", "folder.png"]',
    'folder_playlists': '["playlist_16x9.m3u", "playlist_4x3.m3u", "playlist.m3u"]',
    'sort_keys': '["sorttitle", "date", "title"]',
    'auto_play': '',
    'logging_level': 'INFO'
}
cfg['App'] = {}
cfg.read(CFG_FILE)

# Define the logging level.
try:
    LOG_LEVEL = map_logging[cfg['App']['logging_level']]
except:
    LOG_LEVEL = map_logging['INFO']
logging.basicConfig(format='%(levelname)s: %(message)s', level=LOG_LEVEL)

try:
    # Default pictures directory.
    PICTURES_ROOT = cfg['App']['pictures_root']
    # Playlist player command.
    PLAYER_CMD = cfg['App']['player_cmd']
    # GUI strings.
    APP_TITLE = cfg['App']['title']
    SKIN = cfg['App']['skin']
    LBL_TITLE_PREFIX = cfg['App']['lbl_title_prefix']
    LBL_SORT_BY = cfg['App']['lbl_sort_by']
    LBL_REVERSE = cfg['App']['lbl_reverse']
    # List of filenames to search for playlists.
    FOLDER_PLAYLISTS = json.loads(cfg['App']['folder_playlists'])
    # List of filenames to search for folder thumbnails.
    FOLDER_THUMBNAILS = json.loads(cfg['App']['folder_thumbnails'])
    # List of keys (from nfo files) that can be used for sorting.
    SORT_KEYS = json.loads(cfg['App']['sort_keys'])
    # Playlist to play on start, relative to pictures_root.
    AUTO_PLAY = cfg['App']['auto_play']
except Exception as ex:
    logging.error('Cannot parse configuration file "%s": %s' % (CFG_FILE, str(ex)))
    sys.exit(1)

# Directory name for partent folder.
PARENT_DIR = '..'

# If pictures directory is not defined, try $HOME/Pictures.
if PICTURES_ROOT is None or PICTURES_ROOT == '':
    if 'HOME' in os.environ:
        PICTURES_ROOT = os.path.join(os.environ['HOME'], 'Pictures')

# If autoplay is requested, check if the file esists.
AUTO_PLAYLIST = None
if AUTO_PLAY != '':
    AUTO_PLAYLIST = os.path.join(PICTURES_ROOT, AUTO_PLAY)
    if not os.path.exists(AUTO_PLAYLIST):
        logging.warning('Playlist does not exists: "%s"' % (AUTO_PLAYLIST))
        AUTO_PLAYLIST = None


class Worker(QObject):

    refresh_ui = pyqtSignal()
    finished = pyqtSignal()

    def run(self):
        """ Call the MainWindow.refreshUI() long-running task """
        # NOTICE: Wait some time to ensure that the wait icon is visible.
        # This sleep is actually required only during the MainWindow.__init__()
        # when the call to self.app.processEvents() does not work.
        time.sleep(0.10)
        self.refresh_ui.emit()
        self.finished.emit()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        if not os.path.isdir(PICTURES_ROOT):
            logging.error('Pictures directory does not exists: "%s"s' % (PICTURES_ROOT,))
            sys.exit(1)

        self.setWindowTitle(APP_TITLE)
        self.sort_key = SORT_KEYS[0]
        self.sort_reverse = False

        # Get the screen size to calculate skin aspect.
        self.app = QApplication.instance()
        self.screen_width = self.app.primaryScreen().size().width()
        self.screen_height = self.app.primaryScreen().size().height()
        logging.info('Screen size: %dx%d' % (self.screen_width, self.screen_height))

        # The skin parameters are defined and calculated by a separate module.
        skin_path = 'open_digital_frame.resources.addons.' + SKIN
        logging.info('Importing skin module "%s"' % (skin_path,))
        skin_mod = importlib.import_module(skin_path)
        self.skin = skin_mod.skin(screen_width=self.screen_width)

        # Calculate the QFontMetrics for the thumbnails captions.
        font = self.font()
        font.setFamily(self.skin.ITEM_CAPTION_FONT_FAMILY)
        font.setWeight(map_weight[self.skin.ITEM_CAPTION_FONT_WEIGHT])
        font.setPixelSize(self.skin.ITEM_CAPTION_FONT_SIZE)
        self.caption_font_metrics = QFontMetrics(font)

        # Place the window (normal size) into the desktop available space.
        desktop_width = self.app.desktop().availableGeometry().width()
        desktop_height = self.app.desktop().availableGeometry().height()
        logging.debug('Desktop size: %dx%d' % (desktop_width, desktop_height))
        self.setGeometry(int(desktop_width * 0.01), int(desktop_height * 0.06), int(desktop_width * 0.64), int(desktop_height * 0.68))

        self.toggleFullscreen()
        self.main_window_refresh_mutex = QMutex()

        # Set initial directory and initial focused item.
        self.focused_item_in_dir = {}
        if AUTO_PLAYLIST is not None:
            dir_name = os.path.dirname(AUTO_PLAYLIST)
            current_path = os.path.dirname(dir_name)
            self.focused_item_in_dir[current_path] = os.path.basename(dir_name)
            # The autoplay will wait this mutex lock before start.
            self.main_window_refresh_mutex.lock()
            # Allow 1000 ms before trying the autoplay.
            self.timer = QTimer()
            self.timer.singleShot(1000, self.autoPlay)
        else:
            current_path = PICTURES_ROOT

        # Within __init__() the scroll area is used just to display the wait icon.
        self.scroll = QScrollArea()
        self.setCentralWidget(self.scroll)
        self.initUI(current_path)


    def autoPlay(self):
        """ Start the autoplay of the requested playlist """
        logging.debug('Check if MainWindow() refresh is complete before starting autoplay')
        # Wait max 100 ms for the MainWindow refresh mutex is released.
        if self.main_window_refresh_mutex.tryLock(100):
            self.main_window_refresh_mutex.unlock()
            logging.info('Starting autoplay')
            self.selectItem(self.focused_item)
        else:
            logging.debug('MainWindow refresh is not complete: delay the autoplay by 1 sec.')
            self.timer.singleShot(1000, self.autoPlay)


    def initUI(self, path):
        """ Display the wait icon and start a new thread to refresh the UI """
        # The mutex lock is used to indicate that the UI refresh is running.
        self.main_window_refresh_mutex.tryLock()
        self.current_path = path
        # Show a shadow background and the wait icon.
        # Actually we use a trick to hide the wait icon; after the icon is
        # displayed, the UI starts to redreaw almost immediately, but the
        # screen is not refreshed untill the function is completed.
        # When finally the screen is refreshed, the wait icon does not
        # longer exists, so it disappears.
        icon = QPixmap(self.skin.ICON_WAIT).scaled(self.skin.THUMB_WIDTH, self.skin.THUMB_HEIGHT, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)
        dim_background = QLabel(self.scroll)
        dim_background.move(0, 0)
        dim_background.resize(self.screen_width, self.screen_height)
        dim_background.setStyleSheet(self.skin.STYLE_WAIT_BACKGROUND)
        dim_background.setHidden(False)
        wait_icon = QLabel(self.scroll)
        wait_icon.setPixmap(icon)
        wait_icon.move((self.screen_width - icon.width()) // 2, (self.screen_height - icon.height()) // 2)
        wait_icon.setHidden(False)
        # Force GUI refresh (not working during the first __init__() execution).
        self.app.processEvents()
        # Create a new thread to call the refreshUI().
        # https://realpython.com/python-pyqt-qthread/
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)
        self.thread.started.connect(self.worker.run)
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        self.worker.refresh_ui.connect(self.refreshUI)
        self.thread.start()


    def refreshUI(self):
        """ Initialize the user interface """
        self.ui_items = []
        self.focused_item = None
        self.scroll = QScrollArea()
        self.widget = QWidget()
        self.grid = QGridLayout()
        self.grid.setSpacing(self.skin.GRID_ITEM_SPACING)
        self.grid.setContentsMargins(self.skin.GRID_HORIZONTAL_MARGIN, self.skin.GRID_ITEM_SPACING, self.skin.GRID_HORIZONTAL_MARGIN, self.skin.GRID_ITEM_SPACING)
        self.widget.setStyleSheet(self.skin.STYLE_GRID)

        # Install event filter to catch key presses.
        self.scroll.installEventFilter(self)

        # Prepare the "playable" icon.
        playable_pixmap = QPixmap(self.skin.ICON_PLAYABLE).scaled(self.skin.ICON_PLAYABLE_SIZE, self.skin.ICON_PLAYABLE_SIZE, aspectRatioMode=Qt.KeepAspectRatio, transformMode=Qt.SmoothTransformation)

        # Get the dir_items: a dictionary where the keys are the directory
        # names and each element is a dictionary of nfo elements.
        dir_items = read_directory_nfo(self.current_path)
        order = 'descending' if self.sort_reverse else 'ascending'
        logging.debug('Sorting items by %s, %s' % (self.sort_key, order))
        sorted_keys = sorted(dir_items, key=lambda k: dir_items[k][self.sort_key], reverse=self.sort_reverse)
        # Move the '..' (PARENT_DIR) item to the top of the list, regardless of sorting.
        if PARENT_DIR in sorted_keys:
            sorted_keys.remove(PARENT_DIR)
            sorted_keys.insert(0, PARENT_DIR)
        #print(dir_items)
        #print('sorted_keys: %s' % (sorted_keys,))

        # Should eventually restore the focus on the previously focused item.
        if self.current_path in self.focused_item_in_dir:
            dir_to_focus = self.focused_item_in_dir[self.current_path]
        else:
            dir_to_focus = None
        index_to_focus = 0

        i = 0
        for key in sorted_keys:
            if key == dir_to_focus:
                index_to_focus = i
            dir_item = dir_items[key]
            # Each grid item is contained into a QVBoxLayout.
            item_layout = QVBoxLayout()
            item_layout.setSpacing(0)

            # Read and scale the thumbnail image.
            thumbnail_image = self.skin.ICON_BROKEN_IMAGE
            if 'thumbnail' in dir_item:
                thumb = dir_item['thumbnail']
                if thumb is None:
                    if dir_item['dir'] == PARENT_DIR:
                        thumbnail_image = self.skin.ICON_DEFAULT_FOLDER_BACK
                    else:
                        thumbnail_image = self.skin.ICON_DEFAULT_FOLDER
                elif os.path.exists(thumb):
                    thumbnail_image = thumb
            pixmap = QPixmap(thumbnail_image)
            if pixmap.isNull():
                pixmap = QPixmap(self.skin.ICON_BROKEN_IMAGE)
            # Values for aspectRatioMode: Qt.KeepAspectRatio, Qt.IgnoreAspectRatio
            thumbnail = pixmap.scaled(self.skin.THUMB_WIDTH_FOCUSED, self.skin.THUMB_HEIGHT_FOCUSED, aspectRatioMode=Qt.IgnoreAspectRatio, transformMode=Qt.SmoothTransformation)

            # Thumbnail image for the item.
            item_pixmap = QLabel()
            item_pixmap.setFixedSize(self.skin.ITEM_PIXMAP_WIDTH, self.skin.ITEM_PIXMAP_HEIGHT)
            item_pixmap.setScaledContents(True)
            item_pixmap.setPixmap(thumbnail)
            item_pixmap.setStyleSheet(self.skin.STYLE_PIXMAP_LABEL)

            # Text label for the item caption.
            item_caption = QLabel(text=dir_item['title'])
            item_caption.setFixedSize(self.skin.ITEM_CAPTION_WIDTH, self.skin.ITEM_CAPTION_HEIGHT)
            item_caption.setStyleSheet(self.skin.STYLE_TEXT_LABEL)
            item_caption.setWordWrap(True)
            item_caption.setAlignment(Qt.AlignCenter)
            # Get the size of the rectangle required to contain the label.
            rect = self.caption_font_metrics.boundingRect(QRect(0, 0, self.skin.THUMB_WIDTH, self.skin.CAPTION_HEIGHT), Qt.TextWordWrap, item_caption.text())
            # If caption height is more than the allowed space, align to top.
            if rect.height() > self.skin.CAPTION_HEIGHT:
                item_caption.setAlignment(Qt.AlignHCenter)

            # If exists a playlist, show the "playable" icon.
            if 'playlist' in dir_item and dir_item['playlist'] is not None:
                slideshow_icon = QLabel(item_pixmap)
                slideshow_icon.setPixmap(playable_pixmap)
                slideshow_icon.setStyleSheet(self.skin.STYLE_ICON_PLAYABLE)
                slideshow_icon.move(0, 0)

            item_layout.addStretch()
            item_layout.addWidget(item_pixmap, alignment=Qt.AlignCenter)
            item_layout.addWidget(item_caption, alignment=Qt.AlignCenter)
            item_layout.addStretch()

            # Add an item_index attribute to both pixmap and text label, used when catching mouse clicks.
            item_pixmap.item_index = i
            item_caption.item_index = i
            self.ui_items.append({'pixmap': item_pixmap, 'caption': item_caption, 'nfo': dir_item})

            # Install and event filter on the labels to catch mouse clicks.
            item_pixmap.installEventFilter(self)
            item_caption.installEventFilter(self)

            x = i % self.skin.COLUMNS
            y = i // self.skin.COLUMNS
            self.grid.addLayout(item_layout, y, x)
            i += 1

        # Eventually fill the grid to COLUMNS with empty widgets.
        if i < self.skin.COLUMNS:
            for x in range(i, self.skin.COLUMNS):
                self.grid.addWidget(QWidget(), 0, x)

        # Set the minimum size for the cells of the grid.
        for column in range(0, self.skin.COLUMNS):
            self.grid.setColumnMinimumWidth(column, self.skin.CELL_MIN_WIDTH)
        for row in range(0, math.ceil(float(len(self.ui_items)) / self.skin.COLUMNS)):
            self.grid.setRowMinimumHeight(row, self.skin.CELL_MIN_HEIGHT)

        # Add a stretching space to the bottom of the grid page.
        page_layout = QVBoxLayout()
        page_layout.setSpacing(0)
        page_layout.addLayout(self.grid)
        page_layout.addStretch()
        self.widget.setLayout(page_layout)

        # Scroll Area Properties.
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # The scroll area will automatically resize the widget in order to avoid scroll bars.
        self.scroll.setWidgetResizable(True)
        # The widget becomes a child of the scroll area.
        self.scroll.setWidget(self.widget)
        # Hide the frame of the scroll area.
        self.scroll.setFrameStyle(QFrame.NoFrame)
        # Sets the scroll area to be the main window’s central widget.
        self.setCentralWidget(self.scroll)

        # Display the window title over the scroll area.
        window_title_shadow = QLabel(self.scroll)
        window_title_shadow.move(0, 0)
        gradient = QPixmap(self.skin.GRADIENT_IMAGE).scaled(self.screen_width, self.skin.GRADIENT_HEIGHT, aspectRatioMode=Qt.IgnoreAspectRatio, transformMode=Qt.SmoothTransformation)
        window_title_shadow.setPixmap(gradient)
        window_title = QLabel(self.scroll)
        p_root = pathlib.Path(PICTURES_ROOT)
        p_cur = pathlib.Path(self.current_path)
        prefix_len = len(str(p_root)) - len(p_root.name)
        rel_dir = str(p_cur)[prefix_len:]
        title_text = '%s: %s' % (LBL_TITLE_PREFIX, rel_dir)
        window_title.setText(title_text)
        window_title.setStyleSheet(self.skin.STYLE_WINDOW_TITLE)
        window_title.adjustSize()
        window_title.move(0, 0)
        # Get the label size and eventually truncate the path.
        label_width = window_title.size().width()
        label_height = window_title.size().height()
        if label_width > (self.screen_width * 0.98):
            title_len = len(title_text)
            max_len = int(self.screen_width / (label_width / title_len)) - 6
            title_text = '%s: ...%s' % (LBL_TITLE_PREFIX, rel_dir[title_len-max_len:])
            window_title.setText(title_text)
        # Display the subtitle (sorting order, etc.)
        window_subtitle = QLabel(self.scroll)
        sort_label = self.sort_key.capitalize()
        if self.sort_reverse:
            sort_label += ' (%s)' % (LBL_REVERSE,)
        window_subtitle.setText('%s: %s' % (LBL_SORT_BY, sort_label,))
        window_subtitle.setStyleSheet(self.skin.STYLE_WINDOW_SUBTITLE)
        window_subtitle.move(0, label_height)

        self.show()
        # Set the actual UI focus and the "logical" focus.
        self.widget.setFocus()
        self.moveFocus(index_to_focus)
        # UI refresh is complete, release the mutex lock.
        self.main_window_refresh_mutex.unlock()


    def moveFocus(self, new_index):
        """ Repaint the items when logical focus moves """
        if self.focused_item is not None:
            # Remove focus from the focused item.
            item_pixmap = self.ui_items[self.focused_item]['pixmap']
            item_caption = self.ui_items[self.focused_item]['caption']
            item_pixmap.setFixedSize(self.skin.ITEM_PIXMAP_WIDTH, self.skin.ITEM_PIXMAP_HEIGHT)
            item_pixmap.setStyleSheet(self.skin.STYLE_PIXMAP_LABEL)
            item_caption.setStyleSheet(self.skin.STYLE_TEXT_LABEL)
            item_caption.setFixedSize(self.skin.ITEM_CAPTION_WIDTH, self.skin.ITEM_CAPTION_HEIGHT)
        self.focused_item = new_index
        # Set focus to the new focused item.
        item_pixmap = self.ui_items[self.focused_item]['pixmap']
        item_caption = self.ui_items[self.focused_item]['caption']
        item_pixmap.setFixedSize(self.skin.ITEM_PIXMAP_WIDTH_FOCUSED, self.skin.ITEM_PIXMAP_HEIGHT_FOCUSED)
        item_pixmap.setStyleSheet(self.skin.STYLE_PIXMAP_LABEL_FOCUSED)
        item_caption.setStyleSheet(self.skin.STYLE_TEXT_LABEL_FOCUSED)
        item_caption.setFixedSize(self.skin.ITEM_CAPTION_WIDTH_FOCUSED, self.skin.ITEM_CAPTION_HEIGHT_FOCUSED)
        # Scroll the area to make the focused item visible.
        # TODO: Is it possible to use the container?
        self.scroll.ensureWidgetVisible(self.ui_items[self.focused_item]['pixmap'])
        self.scroll.ensureWidgetVisible(self.ui_items[self.focused_item]['caption'])


    def selectItem(self, item_index):
        """ Double click or Return key over an item  """
        nfo = self.ui_items[item_index]['nfo']
        # If the selected item has a playlist, play it.
        if 'playlist' in nfo and nfo['playlist'] is not None:
            playlist = os.path.join(nfo['path'], nfo['playlist'])
            if os.path.exists(playlist):
                logging.info('Starting playlist "%s"' % (playlist,))
                # Build the player command line replacing the filename placeholder.
                cmd = []
                filename_replaced = False
                for part in PLAYER_CMD.split():
                    if part == '{f}':
                        cmd.append(playlist)
                        filename_replaced = True
                    else:
                        cmd.append(part)
                if not filename_replaced:
                    # Add playlist to the end of the command line.
                    cmd.append(playlist)
                logging.debug('Starting command "%s"' % (cmd,))
                retcode = subprocess.call(cmd)
                return
        # The selected item is a simple directory.
        new_path = nfo['path']
        if os.path.isdir(new_path):
            # Remember focused item for this directory before changing.
            focused_dir = self.ui_items[self.focused_item]['nfo']['dir']
            self.focused_item_in_dir[self.current_path] = focused_dir
            logging.debug('Switching from directory "%s" to "%s"' % (self.current_path, new_path))
            self.initUI(new_path)
        else:
            logging.warning('Selected path "%s" does not exists' % (new_path,))


    def updateSortKey(self, cycle=False, invert=False):
        """ Cycle through the sorting keys and set ascending or descending order """
        logging.info('Changing sorting criteria')
        if cycle:
            new_index = SORT_KEYS.index(self.sort_key) + 1
            if new_index >= len(SORT_KEYS):
                new_index = 0
            self.sort_key = SORT_KEYS[new_index]
        if invert:
            self.sort_reverse = not self.sort_reverse
        # Remember focused item before sorting.
        focused_dir = self.ui_items[self.focused_item]['nfo']['dir']
        self.focused_item_in_dir[self.current_path] = focused_dir
        self.initUI(self.current_path)


    def eventFilter(self, source, event):
        """ Process mouse and keyboard events """
        if hasattr(source, 'item_index'):
            # An event occurred over an item of the list.
            if event.type() == QEvent.MouseButtonPress:
                self.moveFocus(source.item_index)
            elif event.type() == QEvent.MouseButtonDblClick:
                self.selectItem(source.item_index)
        elif event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Enter or event.key() == Qt.Key_Return:
                self.selectItem(self.focused_item)
            elif event.key() == Qt.Key_Backspace:
                # If the first item is the parent directory, switch to it.
                if self.ui_items[0]['nfo']['dir'] == PARENT_DIR:
                    self.selectItem(0)
            elif event.key() == Qt.Key_S:
                self.updateSortKey(cycle=True)
            elif event.key() == Qt.Key_R:
                self.updateSortKey(invert=True)
            elif event.key() == Qt.Key_Right:
                # Next item.
                if self.focused_item < (len(self.ui_items) - 1):
                    self.moveFocus(self.focused_item + 1)
            elif event.key() == Qt.Key_Left:
                # Previous item.
                if self.focused_item > 0:
                    self.moveFocus(self.focused_item - 1)
            elif event.key() == Qt.Key_Down:
                # Next row.
                if self.focused_item < (len(self.ui_items) - 1):
                    new_focus = self.focused_item + self.skin.COLUMNS
                    if new_focus >= len(self.ui_items):
                        new_focus = len(self.ui_items) - 1
                    self.moveFocus(new_focus)
            elif event.key() == Qt.Key_Up:
                # Previous row.
                if self.focused_item > 0:
                    new_focus = self.focused_item - self.skin.COLUMNS
                    if new_focus < 0:
                        new_focus = 0
                    self.moveFocus(new_focus)
            elif event.key() == Qt.Key_Home:
                # Focus to the first element.
                self.moveFocus(0)
            elif event.key() == Qt.Key_End:
                # Focus to the last element.
                self.moveFocus(len(self.ui_items) - 1)
            elif event.key() == Qt.Key_F11 or event.key() == Qt.Key_F:
                self.toggleFullscreen()
            else:
                #logging.debug('KeyPress: %s [%r]' % (event.key(), source))
                pass
        return super().eventFilter(source, event)


    def toggleFullscreen(self):
        """ Toggle the full screen status """
        if self.isFullScreen():
            self.app.restoreOverrideCursor()
            self.showNormal()
        else:
            self.app.setOverrideCursor(QCursor(Qt.BlankCursor))
            self.showFullScreen()


def read_directory_nfo(path):
    """ Find all the subdirectories in path (not recursive) collecting the nfo data """
    result = {}
    p = pathlib.Path(path)
    if path == PICTURES_ROOT:
        # This is the root directory.
        pass
    else:
        # Add an item for the parent folder.
        result[PARENT_DIR] = {'dir': PARENT_DIR, 'title': '', 'sorttitle': '', 'date': '1970-01-01', 'thumbnail': None, 'path': str(p.parent), 'playlist': None}
    dir_list = [item for item in p.iterdir() if item.is_dir()]
    for item in dir_list:
        dir_name = item.name
        dir_name = os.fsencode(dir_name).decode('utf-8')
        result[dir_name] = get_directory_info(os.path.join(path, dir_name))
    return result


def get_directory_info(path):
    """ Read the path/folder.nfo file and return a dictionary """
    nfo = {}
    # Initialize some values to defaults.
    nfo['dir'] = os.path.basename(path)
    nfo['title'] = os.path.basename(path).replace("_", " ")
    nfo['path'] = path
    nfo['sorttitle'] = None
    nfo['date'] = None
    nfo['tags'] = []
    nfo['thumbnail'] = None
    nfo['playlist'] = None
    nfo['slides'] = None
    for name in FOLDER_THUMBNAILS:
        dir_thumb = os.path.join(path, name.strip())
        if os.path.exists(dir_thumb.encode('utf-8')):
            nfo['thumbnail'] = dir_thumb
            break
    for name in FOLDER_PLAYLISTS:
        playlist = name.strip()
        playlist_path = os.path.join(path, playlist)
        if os.path.exists(playlist_path.encode('utf-8')):
            nfo['playlist'] = playlist
            nfo['slides'] = playlist_length(playlist_path)
            break
    # Read the .nfo xml file for actual values.
    nfo_file = os.path.join(path, 'folder.nfo')
    if os.path.exists(nfo_file.encode('utf-8')):
        try:
            root = ET.parse(nfo_file.encode('utf-8')).getroot()
        except Exception as ex:
            logging.error('Failed to parse file "%s"' % (nfo_file,))
            root = {}
        for child in root:
            if child.tag in ['title', 'sorttitle']:
                nfo[child.tag] = child.text.strip()
            elif child.tag == 'tag':
                nfo['tags'].append(child.text.strip())
            elif child.tag == 'date':
                date_string = child.text.strip()
                if re.match('\d{4}$', date_string):
                    nfo['date'] = '%s-01-01' % (date_string,)
                elif re.match('\d{4}-\d{2}-\d{2}$', date_string):
                    nfo['date'] = date_string
    if nfo['sorttitle'] is None:
        nfo['sorttitle'] = nfo['title']
    if nfo['date'] is None:
        nfo['date'] = datetime.datetime.fromtimestamp(os.stat(path.encode('utf-8')).st_mtime).strftime('%Y-%m-%d')
    return nfo


def playlist_length(playlist):
    """ Return the number of images into the playlist with a defined geometry """
    slide_count = 0
    with open(playlist.encode('utf-8'), mode="r", encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if re.search("[^#].*\|\d", line):
                slide_count += 1
    return slide_count


def main():
    app = QApplication(sys.argv)
    main = MainWindow()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
