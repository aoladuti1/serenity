# support
import os
import sys
import pathlib
from time import sleep
from serenityapp.lang import L
from tkinter import *
import ttkbootstrap as ttk
from typing import TypeVar
from serenityapp.themes import USER_THEMES

# useful functions


def is_past_list(index, list) -> bool:
    return index > len(list) - 1


def is_last_index(index, list) -> bool:
    return index == len(list) - 1


def next_valid_index(from_index: int, circular_list: list) -> int:
    if from_index < len(circular_list) - 1:
        return from_index + 1
    else:
        return 0


def path_exists(path):
    return os.path.exists(os.path.expanduser(path))


def light_wait():
    sleep(0.001)


def is_netpath(path):
    return '://' in path[0:13]


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
if getattr(sys, 'frozen', False):
    DIR_PATH = os.path.dirname(sys.executable) + os.sep
else:
    DIR_PATH = os.getcwd() + os.sep
# should change to os.cwd() + "art" + os.sep in future
ART_PATH = DIR_PATH + "art" + os.sep

PLAYLIST_FOLDER_NAME = L['PLAYLISTS']
PLAYLISTS_PATH = DIR_PATH + PLAYLIST_FOLDER_NAME + os.sep

DL_FOLDER_NAME = L['DOWNLOADS']
DOWNLOAD_PATH = DIR_PATH + DL_FOLDER_NAME + os.sep

# modifying PATH
os.environ['PATH'] = DIR_PATH + 'subprograms' + \
    os.sep + 'libmpv' + os.pathsep + os.environ['PATH']
os.environ['PATH'] = DIR_PATH + 'subprograms' + os.sep + \
    'ffmpeg' + os.sep + 'bin' + os.pathsep + os.environ['PATH']

# file paths
DEFAULT_ART = 'default_art.jpg'  # to be removed
DATABASE = DIR_PATH + "databases" + os.sep + "data.sqlite"

# special
FIRST_USE = not path_exists(DATABASE)

# gui
THEME_NAME = 'serenity'
COLOUR_DICT = USER_THEMES['serenity']['colors']
DELETING_HEX = '#ff4040'
SELECTED_LABEL_BG_HEX = '#1a1836'
UNSELECTED_LABEL_BG_HEX = '#000000'
ACTIVE_BUTTON_BG_HEX = '#0b3740'
CLICK_BUTTON_BG_HEX = '#2696ad'
DEFAULT_FONT_FAMILY = 'Cascadia Code Light'
SMALL_SCREEN_CUTOFF = 2000


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
    import serenityapp.mastertools as mastertools
    root.attributes('-alpha', 0)
    root.iconbitmap(DIR_PATH + 'icon.ico')
    root.title("serenity")
    root.configure(background=COLOUR_DICT['bg'])
    root.columnconfigure(0, weight=1)
    mastertools.init(root, expanded)
