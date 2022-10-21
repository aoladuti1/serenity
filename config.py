# support
import os
import pathlib
from tkinter import *
import ttkbootstrap as ttk
from typing import TypeVar
from themes.user import USER_THEMES


def path_exists(path):
    return os.path.exists(os.path.expanduser(path))


# typing
PathLike = TypeVar("PathLike", str, pathlib.Path)

SUPPORTED_EXTENSIONS = (
    ".mp3", ".wav", ".aac",
    ".wma", ".flac", ".ogg",
    ".opus", ".m4a", ".wma",
    ".pcm", ".au", ".3gp",
)  # THIS IS FAR FROM EXHAUSTIVE

DOWNLOADS_CODEC = 'mp3'

ART_FORMAT = 'jpg'

# only splitterchar should be changed by the user
SPLITTER_CHAR = '-'
SPLITTER = " " + SPLITTER_CHAR + " "

# placeholders
UNKNOWN_ARTIST = "Unknown Artist"
UNKNOWN_ALBUM = "---"
UNKNOWN_ALBUM_ARTIST = "---"

# directories
# path to config w/ slash appended
DIR_PATH = os.path.dirname(os.path.realpath(__file__)) + os.sep
# should change to os.cwd() + "art" + os.sep in future
ART_PATH = DIR_PATH + "art" + os.sep

PLAYLIST_FOLDER_NAME = '-playlists-'
PLAYLISTS_PATH = DIR_PATH + PLAYLIST_FOLDER_NAME + os.sep

DL_FOLDER_NAME = '-downloads-'
DOWNLOAD_PATH = DIR_PATH + DL_FOLDER_NAME + os.sep

THEMES_PATH = DIR_PATH + 'themes' + os.sep

# modifying PATH
os.environ['PATH'] = DIR_PATH + 'subprograms' + \
    os.sep + 'libmpv' + os.pathsep + os.environ['PATH']
os.environ['PATH'] = DIR_PATH + 'subprograms' + os.sep + \
    'ffmpeg' + os.sep + 'bin' + os.pathsep + os.environ['PATH']

# file paths
DEFAULT_ART = THEMES_PATH + 'default_art.jpg'
DATABASE = DIR_PATH + "databases" + os.sep + "data.sqlite"

# gui
THEME_NAME = 'serenity'
COLOUR_DICT = USER_THEMES['serenity']['colors']
SELECTED_LABEL_BG_HEX = '#1a1836'
UNSELECTED_LABEL_BG_HEX = '#000000'
ACTIVE_BUTTON_BG_HEX = '#0b3740'
CLICK_BUTTON_BG_HEX = '#2696ad'
DEFAULT_FONT_FAMILY = 'Cascadia Code Light'
EXPAND = 'expand'
CONTRACT = 'contract'
SMALL_SCREEN_CUTOFF = 2000

# text
SEARCH_ICON = u"\U0001F50E"
CONVERSION_WARNING = ['Hold on!',
                      'Files are still converting/downloading. Quit?']
GUIDE_TEXT = """Click 'More...' to add some music!

Then, click [add library] if each song file is in an album-named folder, and each album-named folder is inside an artist-named folder. For example (assuming you add a directory called "Music") the full directory of the song "Don't" may be "Music/Bryson Tiller/T R A P S O U L/05 - Don't.mp3."

Otherwise, click [add songs] and we'll try our best to get all your music added and organised nicely :-)

When you choose a directory all music files in its subdirectories will be added to the database.

Don't worry too much about the EXACT file / folder names, Serenity is flexible!
[Note: Serenity does not use metadata at all. Things like track number can be signalled by being present in the filename like .../01 - Intro.mp3.]"""


def configureStyle():
    style = ttk.Style(THEME_NAME)
    # the following line stops annoying highlight lines on button click
    style.configure('TButton', focuscolor=style.configure(
        'TButton')['background'])
    style.configure('TFrame', background='black')


def configureFont():
    DEFAULT_FONT = ttk.font.nametofont("TkDefaultFont")
    DEFAULT_FONT_SIZE = 14
    DEFAULT_FONT.configure(family=DEFAULT_FONT_FAMILY, size=DEFAULT_FONT_SIZE)


def configureRoot(root: ttk.Window, expanded: bool = False):
    import mastertools
    root.attributes('-alpha', 0)
    root.iconbitmap(THEMES_PATH + "icon.ico")
    root.title("serenity")
    root.configure(background=COLOUR_DICT['bg'])
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=1)
    root.columnconfigure(0, weight=1)
    mastertools.init(root, expanded)
    

