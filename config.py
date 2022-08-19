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
SPLITTERCHAR = '-'
SPLITTER = " " + SPLITTERCHAR + " "

#placeholders
UNKNOWN_ARTIST = "Unknown Artist"
UNKNOWN_ALBUM = "---"
UNKNOWN_ALBUM_ARTIST = "---"

#directories
DIR_PATH = os.path.dirname(os.path.realpath(__file__)) #path to config