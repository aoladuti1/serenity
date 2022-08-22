#support
import os
import subprocess


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
DATABASE = DIR_PATH + "databases" + os.sep + "data.db"
