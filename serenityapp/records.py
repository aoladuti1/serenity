import os
import re
import time
from pathlib import Path

from pymediainfo import MediaInfo

from serenityapp.config import (DOWNLOAD_PATH, SPLITTER, SPLITTER_CHAR,
                                SUPPORTED_EXTENSIONS, UNKNOWN_ALBUM,
                                UNKNOWN_ARTIST, path_exists)
from serenityapp.db import DBLink

numgex = re.compile(r"^\d+")  # matches leading digits
dbLink = DBLink()


def get_audio_info(FQFN):
    media_info = MediaInfo.parse(filename=FQFN)
    for track in media_info.tracks:
        if track.format is None:
            # raise Exception(
            #     """
            #     Error: file not accessible, likely an online-only file
            #     whose storage app (such as OneDrive) either
            #     isn't running properly on this computer or is offline.
            #     It is highly recommended for all files to be offline.
            #     Please retry.
            #     """
            # )
            pass
        elif track.track_type == "Audio":
            # print(track.to_data()) gives the whole dict
            bitRateInfo = track.other_bit_rate[0]
            samplingRateInfo = track.other_sampling_rate[0]
            codec = track.format
            # returning here is an optimization
            return [bitRateInfo, samplingRateInfo, codec]
    return ["0", "0", "0"]


def refresh():
    for directory_tuple in dbLink.get_directories_structures():
        add_folder(directory_tuple[0], bool(directory_tuple[1]))
    dbLink.del_all_absent_songs()


def get_track_info(song):
    """
    Returns an array of ["", track, trackNum]
    """
    trackNum = 0
    try:
        track = song.split(SPLITTER)[-1]
    except IndexError:
        track = song
    if (match := numgex.search(track)) is not None:
        trackNum = int(match.group())
    return ["", track, str(trackNum)]


def get_song_info(song, folder_name):
    """
    Returns an array of [artist, track, trackNumber]
    """

    trackNum = 0
    try:
        track = song.split(SPLITTER)[-1]
        artist = song.split(SPLITTER)[-2]
    except IndexError:
        track = song
        artist = UNKNOWN_ARTIST
    if (match := numgex.search(track)) is not None:
        trackNum = int(match.group())
    if artist == UNKNOWN_ARTIST or artist.isnumeric():
        try:
            artist = folder_name.split(SPLITTER)[-2]
        except Exception:
            pass
    if artist[0].isnumeric() is True and trackNum == 0:
        try:
            artist_attempt = re.search(
                r"\S*\s*(.*)\s+" + SPLITTER_CHAR + r"\s+", song).group(1)
            artist = artist_attempt
            if artist == "":
                artist = UNKNOWN_ARTIST
            trackNum = int(numgex.search(song).group())
        except Exception:
            pass
    return [artist, track, str(trackNum)]


def get_album(folder_name, artist):
    if len(folder_name.split(SPLITTER)) > 1:
        if folder_name.split(SPLITTER)[-2] == artist:
            return folder_name.split(SPLITTER)[-1]
        else:
            return UNKNOWN_ALBUM
    else:
        return UNKNOWN_ALBUM


def __get_song_nostructure(song, folder_name):
    info = get_song_info(song, folder_name)
    artist = info[0]
    album = get_album(folder_name, artist)
    track = info[1]
    trackNum = info[2]
    return [artist, album, track, trackNum]


def get_song(song, file_dir, AAT_structure):
    """
    Get the artist and track from a song.
    A song may be within an AAT_structure structure.
    An AAT_structure (Artist-Album-Track) folder structure means inside each
    Artist folder are all their Album folders, which themselves
    contain audio files like so:
    C:/Bryson Tiller/The Best Album Ever/The Best Track Ever.mp3

    Args:
        song: "bryson tiller - dont" for instance
        file_dir: full path to the folder containing the file

    Returns:
        array of {artist, album, track, trackNum}
    """
    structure = Path(file_dir).parents
    # file_dir has an appended slash so we do -2 instead of -1
    folder_name = file_dir.split(os.sep)[-2]
    if not AAT_structure or len(structure) < 2:
        return __get_song_nostructure(song, folder_name)
    else:
        artist = str(structure[0]).rpartition(os.sep)[-1]
        album = folder_name
        info = get_track_info(song)
        track = info[1]
        trackNum = info[2]
        return [artist, album, track, trackNum]


# Used by add_files() and add_folders() -- see their docs
# note that file_dir must have a slash (os.sep) appended
# Returns:
#     dict: a dictionary containing all song data, where the keys
#         correspond to a Song table column in the database, or None
#         if the file is already present in the database
def __file_processing(
        file_dir: str, filename: str, AAT_structure: bool) -> dict:
    if filename.endswith(SUPPORTED_EXTENSIONS):
        FQFN = file_dir + filename
        if dbLink.song_registered(FQFN) is True:
            return None
        song = filename.rpartition(".")[0]
        (
            bitRateInfo, samplingRateInfo, codec
        ) = get_audio_info(FQFN)
        (
            artist, album, track, trackNum
        ) = get_song(song, file_dir, AAT_structure)
        song_data = {
            "FQFN": FQFN,
            "artist": artist,
            "album": album,
            "track": track,
            "trackNum": trackNum,
            "bitRateInfo": bitRateInfo,
            "samplingRateInfo": samplingRateInfo,
            "codec": codec,
            "listens": 0
        }
        return song_data


def add_files(FQFNs: list[str], AAT_structure=False):
    """Adds audio files and their data to the database.
    Argument FQFNs is intended to be an alias of
    the return value of tkinter.filedialog.askopenfilenames().
    AAT_structure stands for Artist-Album-Track folder structure.
    An AAT_structure folder structure means that inside each Artist
    folder are all their Album folders, which themselves
    contain audio files.

    If you chose 'The Best Song ever.mp3' as a file
    and set AAT_structure = True, it may have the following fully-qualified
    filename:
    'C:\\Music\\Bryson Tiller\\The Best Album Ever\\The Best Song Ever.mp3'

    Audio files themselves should have the following filename format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if
    AAT_structure == False:
        <artist> - <album>

    Args:
        FQFNs (list[str]): all fully qualified filenames to add
        AAT_structure (bool): if True, the chosen folder is
        believed to follow the Artist-Album-Track structure
    """
    for fqfn in FQFNs:
        FQFN = os.path.abspath(fqfn)
        path = FQFN.rpartition(os.sep)
        file_dir = path[0] + os.sep
        filename = path[2]
        song_data = __file_processing(
            file_dir=file_dir,
            filename=filename,
            AAT_structure=AAT_structure)
        if song_data is None:
            return
        dbLink.add_song(song_data)
        if not dbLink.directory_registered(file_dir):
            dbLink.add_directory(file_dir, AAT_structure=AAT_structure)


def add_downloaded_song(FQFN, data, custom_link=None):
    if custom_link is None:
        custom_link = dbLink
    if custom_link.song_registered(FQFN) is True:
        return
    artist, track, trackNum, _ = data
    while not path_exists(FQFN):
        time.sleep(0.1)
    bitRateInfo, samplingRateInfo, codec = get_audio_info(FQFN)
    while bitRateInfo == '0':
        bitRateInfo, samplingRateInfo, codec = get_audio_info(FQFN)
    song_data = {
        "FQFN": FQFN,
        "artist": artist,
        "album": UNKNOWN_ALBUM,
        "track": track,
        "trackNum": trackNum,
        "bitRateInfo": bitRateInfo,
        "samplingRateInfo": samplingRateInfo,
        "codec": codec,
        "listens": 0
    }
    if not custom_link.song_registered(FQFN):
        custom_link.add_song(song_data)


def add_folder(directory: str, AAT_structure=False):
    """Adds audio files and their directories to the database.
    Argument directory is intended to be an alias of the return value
    for tkinter.filedialog.askdirectory().
    AAT_structure stands for Artist-Album-Track folder structure.
    An AAT_structure folder structure means that inside each Artist
    folder are all their Album folders, which themselves
    contain audio files.

    The chosen folder must contain only Artist folders as
    immediate subdirectories.
    E.g. If you chose 'C:\\Music' as a folder and set
    AAT_structure = True, one well-placed
    song below it may have the following fully qualified filename:
    'C:\\Music\\Bryson Tiller\\The Best Album Ever\\The Best Song Ever.mp3'

    Audio files themselves should have the following naming format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if
    AAT_structure == False
        <artist> - <album>

    Args:
        directory (str): the chosen root directory (no slash appended)
        AAT_structure (bool): if True, the chosen folder is thought to follow \
        the Artist-Album-Track structure
    """
    if directory == "":
        return
    i = 0
    for dir, subdirs, files in os.walk(directory):
        absdir = os.path.abspath(dir)  # no appended slash
        file_dir = absdir + os.sep  # full directory with an appended slash
        for filename in files:
            song_data = __file_processing(
                file_dir, filename, AAT_structure)
            if song_data is None:
                continue
            dbLink.add_song(song_data)
        if i == 0:
            if not dbLink.directory_registered(file_dir):
                dbLink.add_directory(file_dir, AAT_structure=AAT_structure)
            i = 1
        else:  # there are no files in the directory
            pass
            # dbLink.del_directory(file_dir)
