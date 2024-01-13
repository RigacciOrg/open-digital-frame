from PyQt5.QtCore import (
    Qt,
    QEvent,
    QTimer)
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSpacerItem,
    QVBoxLayout,
    QWidget)

import logging
import os
import subprocess
import urllib.parse

import xml.etree.ElementTree as ET

__author__ = "Niccolo Rigacci"
__copyright__ = "Copyright 2023 Niccolo Rigacci <niccolo@rigacci.org>"
__license__ = "GPLv3-or-later"
__email__ = "niccolo@rigacci.org"
__version__ = "0.0.1"


class addon():

    def __init__(self, app):

        prefix = 'addon_'
        extension = '.py'
        self.addon_name = os.path.basename(__file__)[len(prefix):-len(extension)]
        self.app = app
        self.pictures_root = self.app.pictures_root

        # Where to find the resources images.
        res_lib = os.path.realpath(os.path.dirname(__file__))
        res_img = os.path.join(os.path.dirname(res_lib), 'img')

        # How to present this add-on into the directory listing.
        self.item = {
            'title': 'Play Tags Selection',
            'dir':  'addon:%s' % (self.addon_name,),
            'path': 'addon:%s' % (self.addon_name,),
            'sorttitle': None,
            'date': None,
            'tags': None,
            'thumbnail': os.path.join(res_img, 'icon_settings_addons43.png'),
            'playlist': None,
            'slides': None
        }


    def run(self):
        """ Show the plugin widget into the app QScrollArea and install the event filter """

        # Define the size of the items (buttons) and font.
        self.COLUMNS = 5
        self.ITEM_WIDTH = int(self.app.screen_width * 0.96 / self.COLUMNS)
        self.ITEM_HEIGHT = int(self.ITEM_WIDTH * 0.25)
        font_size = int(self.ITEM_HEIGHT * 0.25)
        border_width = 12
        self.STYLE_NORMAL_UNFOCUSED   = 'font-size: %dpx; background-color: grey;  border: solid black; border-width: %dpx;' % (font_size, border_width)
        self.STYLE_SELECTED_UNFOCUSED = 'font-size: %dpx; background-color: white; border: solid black; border-width: %dpx;' % (font_size, border_width)
        self.STYLE_NORMAL_FOCUSED     = 'font-size: %dpx; background-color: grey;  border: solid red;   border-width: %dpx;' % (font_size, border_width)
        self.STYLE_SELECTED_FOCUSED   = 'font-size: %dpx; background-color: white; border: solid red;   border-width: %dpx;' % (font_size, border_width)

        self.ui_items = []
        self.app.scroll = QScrollArea()
        self.app.scroll.setFrameStyle(QFrame.NoFrame)
        self.app.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.app.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.app.setCentralWidget(self.app.scroll)

        widget = QWidget()
        widget.setStyleSheet(self.app.skin.STYLE_GRID)
        widget.setMinimumSize(self.app.screen_width, self.app.screen_height)
        page_layout = QVBoxLayout()
        grid_tags = QGridLayout()
        grid_years = QGridLayout()
        grid_buttons = QGridLayout()

        i = 0
        # Add the tag buttons.
        for item in self.getAllTags():
            ui_item = self.itemButton(item, 'tags')
            self.ui_items.append(ui_item)
            grid_tags.addWidget(ui_item, i // self.COLUMNS, i % self.COLUMNS)
            i += 1
        self.fillGridRow(i, grid_tags)
        i = 0
        # Add the year buttons.
        for item in self.getAllYears():
            ui_item = self.itemButton(item, 'years')
            self.ui_items.append(ui_item)
            grid_years.addWidget(ui_item, i // self.COLUMNS, i % self.COLUMNS)
            i += 1
        self.fillGridRow(i, grid_years)
        i = 0
        # Add the action buttons.
        for item in ['Start slideshow', 'Save as auto-play', 'Exit']:
            ui_item = self.itemButton(item)
            self.ui_items.append(ui_item)
            grid_buttons.addWidget(ui_item, i // self.COLUMNS, i % self.COLUMNS)
            i += 1
        self.max_item_index = len(self.ui_items) - 1
        self.fillGridRow(i, grid_buttons)

        # Indexes of selecteable items.
        self.index_cancel = self.max_item_index
        self.index_save_autoplay = self.max_item_index - 1
        self.index_start_slideshow = self.max_item_index - 2

        # Add a stretchable empty row to the bottom, so the items will be top-aligned.
        grid_buttons.setRowStretch(((i - 1) // self.COLUMNS) + 1, 1)

        page_layout.addLayout(grid_tags)
        page_layout.addSpacerItem(QSpacerItem(1, self.ITEM_HEIGHT))
        page_layout.addLayout(grid_years)
        page_layout.addSpacerItem(QSpacerItem(1, self.ITEM_HEIGHT))
        page_layout.addLayout(grid_buttons)
        widget.setLayout(page_layout)

        # Place the widget into the scroll area and set focus.
        self.app.scroll.setWidget(widget)
        widget.setFocus()
        self.focused_item = None
        self.moveFocus(0)

        # Prepare the tooltip popup label with timer and initialize (hide) it.
        self.app.popup_label = self.app.popupMsg(self.app.scroll, self.app)
        self.app.popup_label.showMsg(None)

        # Install the event filter, which will callback self.eventFilter()
        self.app.addon_event_filter = self.eventFilter
        self.app.scroll.installEventFilter(self.app)


    def itemButton(self, text, group=None):
        """ Create a button """
        button = QLabel()
        button.setText(text)
        button.setFixedSize(self.ITEM_WIDTH, self.ITEM_HEIGHT)
        button.setAlignment(Qt.AlignCenter)
        button.setStyleSheet(self.STYLE_NORMAL_UNFOCUSED)
        button.group = group
        button.selected = False
        if text == '':
            button.setVisible(False)
        return button


    def fillGridRow(self, i, grid_layout):
        """ Add invisible buttons to complete the grid row """
        while (i % self.COLUMNS) != 0:
            button = self.itemButton('')
            self.ui_items.append(button)
            grid_layout.addWidget(button, i // self.COLUMNS, i % self.COLUMNS)
            i += 1
        # Add a stretchable empty column to the right, so the items will be left-aligned.
        grid_layout.setColumnStretch(self.COLUMNS, 1)


    def eventFilter(self, source, event):
        """ Process QEvent.KeyPress for this add-on """
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Right:
                self.selectForward(1, self.max_item_index)
            elif event.key() == Qt.Key_Left:
                self.selectBackward(1, 0)
            elif event.key() == Qt.Key_Down:
                self.selectForward(self.COLUMNS, self.max_item_index)
            elif event.key() == Qt.Key_Up:
                self.selectBackward(self.COLUMNS, 0)
            elif event.key() in (Qt.Key_Backspace, Qt.Key_Escape):
                self.closeAddon()
            elif event.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Space):
                if self.focused_item == self.index_cancel:
                    self.closeAddon()
                elif self.focused_item == self.index_start_slideshow:
                    self.startSlideshow()
                elif self.focused_item == self.index_save_autoplay:
                    self.saveAutoplay()
                else:
                    item_label = self.ui_items[self.focused_item]
                    item_label.selected = not item_label.selected
                    self.moveFocus(self.focused_item)
            else:
                #logging.info('KeyPress: %s [%r]' % (event.key(), source))
                pass
        return False


    def selectForward(self, step, max_index):
        """ Move selection forward by step postions """
        if self.focused_item < max_index:
            new_focus = self.focused_item
            while True:
                new_focus += step
                if new_focus > max_index:
                    new_focus = max_index
                    break
                if self.ui_items[new_focus].isVisible():
                    break
            self.moveFocus(new_focus)


    def selectBackward(self, step, min_index):
        """ Move selection backward by step postions """
        if self.focused_item > min_index:
            new_focus = self.focused_item
            while True:
                new_focus -= step
                if new_focus < min_index:
                    new_focus = min_index
                    break
                if self.ui_items[new_focus].isVisible():
                    break
            self.moveFocus(new_focus)


    def moveFocus(self, new_index):
        """ Repaint the items buttons when logical focus moves """
        if self.focused_item is not None:
            item_label = self.ui_items[self.focused_item]
            if item_label.selected:
                item_label.setStyleSheet(self.STYLE_SELECTED_UNFOCUSED)
            else:
                item_label.setStyleSheet(self.STYLE_NORMAL_UNFOCUSED)
        self.focused_item = new_index
        item_label = self.ui_items[self.focused_item]
        if item_label.selected:
            item_label.setStyleSheet(self.STYLE_SELECTED_FOCUSED)
        else:
            item_label.setStyleSheet(self.STYLE_NORMAL_FOCUSED)
        self.app.scroll.ensureWidgetVisible(item_label)


    def startSlideshow(self):
        """ Generate a playlist upon the selected items and play it """
        query = self.selectedQuery(self.getSelectedItems())
        if query != '':
            logging.info('Starting slideshow with query: "%s"' % (query,))
            self.app.playlist = self.generatePlaylist(query)
            self.app.autoPlay()


    def selectedQuery(self, selected_items):
        """ Convert the selected_items dictionary into an URL query string """
        query_dict = {}
        for group in selected_items:
            query_dict[group] = ','.join(selected_items[group])
        return urllib.parse.urlencode(query_dict)


    def saveAutoplay(self):
        """ Save or clear the auto_play option in configuration file """
        query = self.selectedQuery(self.getSelectedItems())
        if query != '':
            url = 'addon:%s?%s' % (self.addon_name, query)
            logging.info('Saving auto_play URL: "%s"' % (url,))
            self.app.popup_label.showMsg('Saving auto_play option...')
            self.app.saveConfigOption('auto_play', url)
        else:
            logging.info('Clearing auto_play option')
            self.app.popup_label.showMsg('Clearing auto_play option...')
            self.app.saveConfigOption('auto_play', '')


    def getAllTags(self):
        """ Return the list of <tag>s found in all folder.nfo files """
        cmd = ['playlist-selection', '--list-tags', '--root', self.pictures_root]
        logging.info('Executing command: %s' % (cmd,))
        try:
            output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
            tags_found = output.strip().split(',')
        except Exception as ex:
            logging.error('Exception running "%s": %s' % (cmd[0], str(ex)))
            tags_found = []
        return tags_found


    def getAllYears(self):
        """ Return all the playlist years reading folder.nfo files """
        #return []
        return ['1998', '1999', '2000', '2001', '2002', '2021', '2022', '2023', '2024']


    def getSelectedItems(self):
        """ Return a dictionary of items selected into the UI """
        selected_items = {}
        for item in self.ui_items:
            if item.selected:
                if item.group not in selected_items:
                    selected_items[item.group] = []
                selected_items[item.group].append(item.text())
        return selected_items


    def generatePlaylist(self, query):
        """ Receive an URL-like query string and generate a .m3u playlist file """
        output_filename = '/tmp/playlist_tags.m3u'
        cmd = ['playlist-selection', '--root', self.pictures_root, '--output', output_filename]
        logging.info('Generating a playlist for query string "%s"' % (query,))
        query_dict = urllib.parse.parse_qs(query)
        query_is_empty = True
        if 'tags' in query_dict:
            csv = query_dict['tags'][0]
            if csv != '':
                query_is_empty = False
                cmd += ['--any', csv]
        if 'years' in query_dict:
            csv = query_dict['years'][0]
            if csv != '':
                query_is_empty = False
                # TODO: Implement --years into the external program.
                #cmd += ['--years', csv]
        if query_is_empty:
            logging.warning('Query is empty')
            output_filename = None
        else:
            logging.info('Executing command: %s' % (cmd,))
            try:
                output = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0].decode('utf-8')
            except Exception as ex:
                logging.error('Exception running "%s": %s' % (cmd[0], str(ex)))
                output_filename = None
        return output_filename


    def closeAddon(self):
        """ Unlink the eventFilter() for this add-on and repaint the MainWindow UI """
        self.app.addon_event_filter = None
        self.app.waitThread(self.app.refreshUI)
