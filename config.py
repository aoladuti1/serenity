#support
import os
import ttkbootstrap as ttk
import subprocess

from themes.user import USER_THEMES


SUPPORTED_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".aac",
    ".wma"
)

#only splitterchar should be changed by the user
SPLITTER_CHAR = '-'
SPLITTER = " " + SPLITTER_CHAR + " "

#placeholders
UNKNOWN_ARTIST = "Unknown Artist"
UNKNOWN_ALBUM = "---"
UNKNOWN_ALBUM_ARTIST = "---"

#directories
DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + os.sep #path to config w/ slash appended
ART_PATH = DIR_PATH + "art" + os.sep #should change to os.cwd() + "art" + os.sep in future

#file paths
DEFAULT_ART = ART_PATH + "default.jpeg"
DATABASE = DIR_PATH + "databases" + os.sep + "data.sqlite"

#gui
THEME_NAME = 'serenity'
COLOUR_DICT = USER_THEMES['serenity']['colors']
SELECTED_LABEL_BG_HEX = '#1a1836'
UNSELECTED_LABEL_BG_HEX = '#000000'
ACTIVE_BUTTON_BG_HEX = '#0b3740'
CLICK_BUTTON_BG_HEX = '#2696ad'
DEFAULT_FONT_FAMILY = 'Cascadia Code Light'

#gui - left pane
LEFT_PANE_WIDTH = 700

def configureStyle():
    style = ttk.Style(THEME_NAME)
        # the following line stops annoying highlight lines on button click
    style.configure('TButton', focuscolor=style.configure('TButton')['background'])
    style.configure('TFrame', background='black')

def configureFont():
    DEFAULT_FONT = ttk.font.nametofont("TkDefaultFont")
    DEFAULT_FONT_SIZE = 14
    DEFAULT_FONT.configure(family=DEFAULT_FONT_FAMILY, size = DEFAULT_FONT_SIZE)
    
def configureRoot(root: ttk.Window):
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    root.geometry("%dx%d" % (700, height * 0.5))
    root.update()
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    root.title("serenity")