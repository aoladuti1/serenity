#support
import os
import pathlib
import ttkbootstrap as ttk
import math
from typing import TypeVar
from themes.user import USER_THEMES


def path_exists(path):
    return os.path.exists(os.path.expanduser(path))


# typing
PathLike = TypeVar("PathLike", str, pathlib.Path)

SUPPORTED_EXTENSIONS = (
    ".mp3",
    ".wav",
    ".aac",
    ".wma"
) # THIS IS FAR FROM EXHAUSTIVE

DOWNLOADS_CODEC = 'mp3'

ART_FORMAT = 'jpg'

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
PLAYLISTS_PATH = DIR_PATH + 'playlists' + os.sep
DL_FOLDER_NAME = '-downloads-'
DOWNLOAD_PATH = DIR_PATH + DL_FOLDER_NAME + os.sep

#modifying PATH
os.environ['PATH'] += DIR_PATH + os.sep + 'subprograms' +os.sep+'libmpv' + os.pathsep
os.environ['PATH'] += DIR_PATH + 'subprograms' + os.sep + 'ffmpeg' + os.sep + 'bin' + os.pathsep

#file paths
DEFAULT_ART = ART_PATH + "default" + os.sep + "default." + ART_FORMAT
DATABASE = DIR_PATH + "databases" + os.sep + "data.sqlite"

#gui
THEME_NAME = 'serenity'
COLOUR_DICT = USER_THEMES['serenity']['colors']
SELECTED_LABEL_BG_HEX = '#1a1836'
UNSELECTED_LABEL_BG_HEX = '#000000'
ACTIVE_BUTTON_BG_HEX = '#0b3740'
CLICK_BUTTON_BG_HEX = '#2696ad'
DEFAULT_FONT_FAMILY = 'Cascadia Code Light'

def LEFT_PANE_WIDTH(root: ttk.Window):
    return math.floor(root.winfo_screenwidth() / 3)

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
    root.geometry("%dx%d" % (LEFT_PANE_WIDTH(root), height * 0.5))
    root.update()
    root.columnconfigure(0, weight=0)
    root.columnconfigure(1, weight=1)
    root.rowconfigure(0, weight=1)
    root.title("serenity")