import os

class skin():

    def __init__(self, screen_width=1920, columns=5, thumbs_pic_ratio=(4.0/3.0)):

        # Where to find the resources images.
        res_lib = os.path.realpath(os.path.dirname(__file__))
        res_img = os.path.join(os.path.dirname(res_lib), 'img')

        # The overall aspect is defined by the following three values only.
        self.SCREEN_WIDTH = screen_width
        self.COLUMNS = columns
        self.THUMBNAIL_RATIO = thumbs_pic_ratio

        # Colors and icons.
        self.GRID_BACKGROUND = '#0b4a61'
        self.ITEM_BORDER_COLOR = '#0f1b1f'
        self.ITEM_BACKGROUND = '#0f1b1f'
        self.ITEM_FOCUSED_BACKGROUND = '#0f85a6'
        self.ITEM_FOCUSED_BORDER_COLOR = '#0f85a6'
        self.ITEM_CAPTION_COLOR = 'white'
        self.POPUP_BACKGROUND = '#c00f1b1f'
        self.POPUP_COLOR = 'white'

        # Debug colors.
        #ITEM_BORDER_COLOR = 'black'
        #ITEM_FOCUSED_BORDER_COLOR = 'grey'

        # Serif, SansSerif, Monospace
        self.FONT_FAMILY = 'SansSerif'
        # Thin, ExtraLight, Light, Normal, Medium, DemiBold, Bold, ExtraBold, Black
        self.ITEM_CAPTION_FONT_WEIGHT = 'Normal'
        self.TITLE_FONT_WEIGHT = 'Thin'

        # Default icons.
        self.ICON_DEFAULT_FOLDER = os.path.join(res_img, 'DefaultFolder43.png')
        self.ICON_DEFAULT_FOLDER_BACK = os.path.join(res_img, 'DefaultFolderBack43.png')
        self.ICON_BROKEN_IMAGE = os.path.join(res_img, 'broken-photo.png')
        self.ICON_WAIT = os.path.join(res_img, 'DefaultAddonsUpdates.png')
        self.ICON_PLAYABLE = os.path.join(res_img, 'DefaultPlaylist_shadow.png')
        self.ICON_DEFAULT_ADDON = os.path.join(res_img, 'icon_settings_addons43.png')

        # The QGridLayout have fixed style margin and spacing that cannot be reduced or removed.
        self.GRID_FIXED_MARGIN = 9
        self.GRID_FIXED_SPACING = 1

        # Grid margin and spacing added to the fixed values.
        self.GRID_HORIZONTAL_MARGIN = int(self.SCREEN_WIDTH * 0.01875)
        self.GRID_ITEM_SPACING = int(self.SCREEN_WIDTH * 0.022)
        # Thumbmails border size.
        self.THUMB_BORDER_SIZE = int(self.SCREEN_WIDTH / 320 )
        self.THUMB_BORDER_SIZE_FOCUSED = self.THUMB_BORDER_SIZE
        # Thumbnails image size.
        self.THUMB_WIDTH_FOCUSED = (self.SCREEN_WIDTH - (self.GRID_FIXED_MARGIN * 2 + self.GRID_FIXED_SPACING * 2 * self.COLUMNS) - (self.GRID_HORIZONTAL_MARGIN * 2) - (self.GRID_ITEM_SPACING * (self.COLUMNS - 1)) - (self.THUMB_BORDER_SIZE_FOCUSED * 2 * self.COLUMNS)) // self.COLUMNS
        self.THUMB_HEIGHT_FOCUSED = int(self.THUMB_WIDTH_FOCUSED / self.THUMBNAIL_RATIO)
        self.THUMB_WIDTH = int(self.THUMB_WIDTH_FOCUSED * 0.88)
        self.THUMB_HEIGHT = int(self.THUMB_WIDTH / self.THUMBNAIL_RATIO)
        # Thumbnails caption height.
        self.CAPTION_HEIGHT = int(self.THUMB_HEIGHT * 0.25)

        # Main window title and popup.
        self.GRADIENT_IMAGE = os.path.join(res_img, 'osdfade.png')
        self.GRADIENT_HEIGHT = int(self.THUMB_HEIGHT * 0.80)
        self.FONT_SIZE_TITLE = self.THUMB_HEIGHT // 5
        self.FONT_SIZE_SUBTITLE = self.THUMB_HEIGHT // 7
        self.FONT_SIZE_POPUP = self.THUMB_HEIGHT // 7

        # Grid items size.
        self.ITEM_CAPTION_FONT_SIZE = int(self.CAPTION_HEIGHT * 0.85) // 2
        self.ITEM_CAPTION_PAD_FOCUSED_L = (self.THUMB_WIDTH_FOCUSED - self.THUMB_WIDTH) // 2
        self.ITEM_CAPTION_PAD_FOCUSED_R = self.THUMB_WIDTH_FOCUSED - self.THUMB_WIDTH - self.ITEM_CAPTION_PAD_FOCUSED_L
        self.ITEM_PIXMAP_WIDTH = self.THUMB_WIDTH + self.THUMB_BORDER_SIZE * 2
        self.ITEM_PIXMAP_HEIGHT = self.THUMB_HEIGHT + self.THUMB_BORDER_SIZE * 2
        self.ITEM_PIXMAP_WIDTH_FOCUSED = self.THUMB_WIDTH_FOCUSED + self.THUMB_BORDER_SIZE_FOCUSED * 2
        self.ITEM_PIXMAP_HEIGHT_FOCUSED = self.THUMB_HEIGHT_FOCUSED + self.THUMB_BORDER_SIZE_FOCUSED + self.THUMB_BORDER_SIZE
        self.ITEM_CAPTION_WIDTH = self.THUMB_WIDTH + self.THUMB_BORDER_SIZE * 2
        self.ITEM_CAPTION_WIDTH_FOCUSED = self.THUMB_WIDTH_FOCUSED + self.THUMB_BORDER_SIZE_FOCUSED * 2
        self.ITEM_CAPTION_HEIGHT = self.CAPTION_HEIGHT + self.THUMB_BORDER_SIZE
        self.ITEM_CAPTION_HEIGHT_FOCUSED = self.CAPTION_HEIGHT + self.THUMB_BORDER_SIZE_FOCUSED
        self.CELL_MIN_WIDTH = self.THUMB_WIDTH_FOCUSED + self.THUMB_BORDER_SIZE_FOCUSED * 2 + 2
        self.CELL_MIN_HEIGHT = self.THUMB_HEIGHT_FOCUSED + self.THUMB_BORDER_SIZE_FOCUSED * 2 + self.THUMB_BORDER_SIZE + self.CAPTION_HEIGHT + 2
        self.ICON_PLAYABLE_SIZE = int(self.THUMB_WIDTH_FOCUSED / 4.2)

        # CSS styles.
        self.STYLE_GRID = 'background-color: %s;' % (self.GRID_BACKGROUND,) 
        self.STYLE_PIXMAP_LABEL = 'background-color: %s; border: %dpx solid %s;' % (self.ITEM_BACKGROUND, self.THUMB_BORDER_SIZE, self.ITEM_BORDER_COLOR)
        self.STYLE_PIXMAP_LABEL_FOCUSED = 'background-color: %s; border: solid %s; border-width: %dpx %dpx %dpx %dpx;' % (self.ITEM_FOCUSED_BACKGROUND, self.ITEM_FOCUSED_BORDER_COLOR, self.THUMB_BORDER_SIZE_FOCUSED, self.THUMB_BORDER_SIZE_FOCUSED, self.THUMB_BORDER_SIZE, self.THUMB_BORDER_SIZE_FOCUSED)
        self.STYLE_TEXT_LABEL = 'font-family: %s; color: %s; background-color: %s; font-weight: %s; font-size: %dpx; border: solid %s; border-width : 0px %dpx %dpx %dpx' % (self.FONT_FAMILY, self.ITEM_CAPTION_COLOR, self.ITEM_BACKGROUND, self.ITEM_CAPTION_FONT_WEIGHT, self.ITEM_CAPTION_FONT_SIZE, self.ITEM_BORDER_COLOR, self.THUMB_BORDER_SIZE, self.THUMB_BORDER_SIZE, self.THUMB_BORDER_SIZE)
        self.STYLE_TEXT_LABEL_FOCUSED = 'font-family: %s; color: %s; background-color: %s; font-weight: %s; font-size: %dpx; border: solid %s; border-width: 0px %dpx %dpx %dpx; padding: 0px %dpx 0px %dpx;' % (self.FONT_FAMILY, self.ITEM_CAPTION_COLOR, self.ITEM_FOCUSED_BACKGROUND, self.ITEM_CAPTION_FONT_WEIGHT, self.ITEM_CAPTION_FONT_SIZE, self.ITEM_FOCUSED_BORDER_COLOR, self.THUMB_BORDER_SIZE_FOCUSED, self.THUMB_BORDER_SIZE_FOCUSED, self.THUMB_BORDER_SIZE_FOCUSED, self.ITEM_CAPTION_PAD_FOCUSED_L, self.ITEM_CAPTION_PAD_FOCUSED_R)
        self.STYLE_WINDOW_TITLE = 'font-family: %s; color: %s; font-weight: %s; font-size: %dpx; padding: 10px;' % (self.FONT_FAMILY, self.ITEM_CAPTION_COLOR, self.TITLE_FONT_WEIGHT, self.FONT_SIZE_TITLE)
        self.STYLE_WINDOW_SUBTITLE = 'font-family: %s; color: %s; font-weight: %s; font-size: %dpx; padding: 10px;' % (self.FONT_FAMILY, self.ITEM_CAPTION_COLOR, self.TITLE_FONT_WEIGHT, self.FONT_SIZE_SUBTITLE)
        self.STYLE_WAIT_BACKGROUND = 'background-color: rgba(0, 0, 0, 160);'
        self.STYLE_ICON_PLAYABLE = 'border-width: 0; background-color: rgba(0, 0, 0, 0);'
        self.STYLE_POPUP = 'font-family: %s; font-size: %dpx; color: %s; background-color: %s; padding: %dpx;' % (self.FONT_FAMILY, self.FONT_SIZE_POPUP, self.POPUP_COLOR, self.POPUP_BACKGROUND, self.FONT_SIZE_POPUP // 2)

        #print('THUMB_FOCUSED: %d x %d, THUMB: %d x %d, GRID_HORIZONTAL_MARGIN: %d, GRID_ITEM_SPACING %d, THUMB_BORDER_SIZE %d, CAPTION_HEIGHT: %d' % (THUMB_WIDTH_FOCUSED, THUMB_HEIGHT_FOCUSED, THUMB_WIDTH, THUMB_HEIGHT, GRID_HORIZONTAL_MARGIN, GRID_ITEM_SPACING, THUMB_BORDER_SIZE, CAPTION_HEIGHT))
