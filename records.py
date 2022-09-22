from tkinter.tix import Tree
from pymediainfo import MediaInfo
import os
import math
import re
import db
from config import *
import requests
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import cred
from pathlib import Path

numgex = re.compile("^\d+") #matches leading digits

def getAudioInfo(FQFN):
    media_info = MediaInfo.parse(filename=FQFN)
    for track in media_info.tracks:
        if track.format == None:
            raise Exception(
                """
                Error: file not accessible, likely an online-only file 
                whose storage app (such as OneDrive) either
                isn't running properly on this computer or is offline.
                It is highly recommended for all library files to be downloaded.
                Please retry.
                """
            )
        elif track.track_type == "Audio":
            #print(track.to_data()) gives the whole dict
            bitRateInfo = track.other_bit_rate[0]
            samplingRateInfo = track.other_sampling_rate[0]
            codec = track.format
            return [bitRateInfo, samplingRateInfo, codec] #returning here is an optimization
    return ["0", "0", "0"]

# Returns false if it fails to find or assign art
# music is either the track name or album name, dependent on if isAlbum is true
def dlArt(music, artist, album, isAlbum):

    if isAlbum is True:
        target = ART_PATH + artist + os.sep + music + os.sep + music + "." + ART_FORMAT
    else:
        target = ART_PATH + artist + os.sep + album + os.sep + music + "." + ART_FORMAT
    if os.path.exists(target) == True: return target
    
    
    artFile = DEFAULT_ART
    auth_manager = SpotifyClientCredentials(
        client_id=cred.CLIENT_ID,
        client_secret=cred.CLIENT_SECRET
    )
    sp = spotipy.Spotify(auth_manager=auth_manager)

    if artist == UNKNOWN_ARTIST:
        artistqtext = ""
    else:
        artistqtext = "artist:" + artist
    if isAlbum == True:
        try:
            results = sp.search(q='album:' + music + ' ' + artistqtext, type='album', limit=1)
            items = results['albums']['items']
        except:
            return artFile
    else:
        try:
            results = sp.search(q=artistqtext + ' ' + 'track:' + music, type='track', limit=2)
            items = results['tracks']['items']
        except:
            return artFile
    neededArtistArt = False
    if len(items) == 0:
        try:
            if artistqtext == "": return artFile
            results = sp.search(q=artistqtext, type="artist", limit = 3)
            items = results['artists']['items']
            if len(items) > 0:
                neededArtistArt = True
        except:
            return artFile             

    if len(items) > 0:
        webRip = items[0]
        if neededArtistArt == False:
            if isAlbum == True:
                image_url = webRip['images'][0]['url']
            else:
                image_url = webRip['album']['images'][0]['url']
        else:
            image_url = webRip['images'][0]['url']
        img_data = requests.get(image_url).content
        try:
            artFile = target
            os.makedirs(os.path.dirname(artFile), exist_ok=True)
            with open(artFile, 'wb') as handler:
                handler.write(img_data)
        except:
            artFile = DEFAULT_ART
    return artFile

def getTrackInfo(song):
    """
    Returns an array of ["", track, trackNum]
    """
    trackNum = 0
    try:       
        track = song.split(SPLITTER)[-1]
    except IndexError:
        track = song
    if not (match := numgex.search(track)) == None:
        trackNum = int(match.group())
    return ["",track, str(trackNum)]    

def getTrackAndArtistInfo(song, folderName):
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
    if not (match := numgex.search(track)) == None:
        trackNum = int(match.group())
    if artist == UNKNOWN_ARTIST:
        try:
            artist = folderName.split(SPLITTER)[-2]
        except:
            ""
    if artist[0].isnumeric() == True and trackNum == 0:
        try:
            artistAttempt = re.search(r"\S*\s*(.*)\s+" + SPLITTER_CHAR + r"\s+", song).group(1)
            artist = artistAttempt
            if artist == "": artist = UNKNOWN_ARTIST
            trackNum = int(numgex.search(song).group())
        except: ""
    return [artist, track, str(trackNum)]

def getAlbum(folderName, folderIsAlbum):
    if folderIsAlbum == True:
            return folderName
    try:
        album = folderName.split(SPLITTER)[-2]
    except IndexError:
        album = UNKNOWN_ALBUM
    return album    


def __getSongNoStructure(song, folderName, folderIsAlbum):
    info = getTrackAndArtistInfo(song, folderName)
    artist = info[0]
    album = getAlbum(folderName, folderIsAlbum)
    track = info[1]
    trackNum = info[2]
    return [artist, album, track, trackNum] 

def getSong(song, fileDir, folderIsAlbum, AAT_structure = True):
    """
    Get the artist and track from a song. A song may be within an AAT_structure structure.
    An AAT_structure (Artist-Album-Track) folder structure means inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files like so (with no exceptions):
    C:/Bryson Tiller/The Best Album Ever/The Best Track Ever.mp3

    Parameters:

    ~song: "bryson tiller - dont" for instance

    ~fileDir: full path to the folder containing the file

    ~folderIsAlbum: if the folder addition is in album mode or not (for corner cases)

    Returns:
    
    array of {artist, album, track, trackNum}
    """
    structure = Path(fileDir).parents
    folderName = fileDir.split(os.sep)[-2] #fileDir has an appended slash so we do -2 instead of -1
    if AAT_structure == False or len(structure) < 2:
        return __getSongNoStructure(song, folderName, folderIsAlbum)
    else:
        artist = str(structure[0]).rpartition(os.sep)[-1]
        album = folderName
        info = getTrackInfo(song)
        track = info[1]
        trackNum = info[2]
        return [artist, album, track, trackNum]


# Used by addFiles() and addFolders() -- see their docs
# note that fileDir must have a slash (os.sep) appended
# Returns:
#     dict: a dictionary containing all song data, where the keys
#         correspond to a Song table column in the database, or None 
#         if the file is already present in the database
def __fileProcessing(
        fileDir: str, fileName: str,
        foldersAreAlbums: bool, AAT_structure: bool,
        findArt: bool, 
    ) -> dict:
    if fileName.endswith(SUPPORTED_EXTENSIONS):
        FQFN = fileDir + fileName
        if db.songRegistered(FQFN) == True:
            return None
        song = fileName.rpartition(".")[0]
        art = DEFAULT_ART
        (
            bitRateInfo, samplingRateInfo, codec
        ) = getAudioInfo(FQFN)
        (
            artist, album, track, trackNum
        ) = getSong(song, fileDir, foldersAreAlbums, AAT_structure)
        hasAlbum = album != UNKNOWN_ALBUM
        if findArt == True:
            if hasAlbum == True:
                musicChoice = album
            else:
                musicChoice = track
            art = dlArt(musicChoice, artist, album, hasAlbum)
        songData = {
            "FQFN": FQFN,
            "artist": artist, 
            "album": album,
            "track": track,
            "trackNum": trackNum, 
            "bitRateInfo": bitRateInfo,
            "samplingRateInfo": samplingRateInfo,
            "codec": codec,
            "art": art, 
            "listens": 0,     
        }
        return songData


def addFiles(FQFNs: list[str], foldersAreAlbums = False, AAT_structure = False,
            findArt = True):
    """Adds audio files and their data to the database.
    Argument FQFNs is intended to be an alias of
    the return value of tkinter.filedialog.askopenfilenames().
    AAT_structure stands for Artist-Album-Track folder structure.
    An AAT_structure folder structure means that inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files (with no exceptions).
    If you chose 'The Best Song ever.mp3' as a file
    and set AAT_structure = True, it may have the following fully-qualified filename:
    'C:\Music\Bryson Tiller\The Best Album Ever\The Best Song Ever.mp3'

        Note: if AAT_structure == True then foldersAreAlbums will be set to False.
        AAT_structure takes precedence.

    Audio files themselves should have the following filename format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if NEITHER argument
    AAT_structure == True nor foldersAreAlbums == True:
        <artist> - <album>
    
    
    Args: 
        FQFNs (list[str]): all fully qualified filenames to add
        foldersAreAlbums (bool): if true, then the name of the \
            immediate folder each music file is contained within \
            is assumed to be its album/body of music
        AAT_structure (bool): if True, the chosen folder is believed to follow \
            the Artist-Album-Track structure
        findArt (bool): if True, will attempt to find \
            album/track/artist art (in that order of priority) \
            on Spotify. Failing this, or if findArt == False \
            default Serenity art is selected.
        
    """
    for fqfn in FQFNs:
        FQFN = os.path.abspath(fqfn)
        pathAndName = FQFN.rpartition(os.sep)
        fileDir=pathAndName[0] + os.sep
        fileName=pathAndName[2]
        songData = __fileProcessing(
            fileDir=fileDir,
            fileName=fileName,
            foldersAreAlbums=foldersAreAlbums,
            AAT_structure=AAT_structure,
            findArt=findArt
        ) # may invert var foldersAreAlbums - see doc
        if songData==None: return
        db.addSong(songData)      
    
def addFolder(directory: str, foldersAreAlbums = False, AAT_structure = False, 
              findArt=True):
    """Adds audio files and their directories to the database.
    Argument directory is intended to be an alias of the return value
    for tkinter.filedialog.askdirectory().
    AAT_structure stands for Artist-Album-Track folder structure.
    An AAT_structure folder structure means that inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files (with no exceptions). 
    The chosen folder must contain only Artist folders as 
    immediate subdirectories.
    E.g. If you chose 'C:\Music' as a folder and set AAT_structure = True, one well-placed 
    song below it may have the following fully qualified filename:
    'C:\Music\Bryson Tiller\The Best Album Ever\The Best Song Ever.mp3'

        Note: if AAT_structure == True then foldersAreAlbums will be set to False.
        AAT_structure takes precedence.

    Audio files themselves should have the following naming format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if neither arguments
    AAT_structure == True nor foldersAreAlbums == True:
        <artist> - <album>
    
    Args: 
        directory (str): the chosen root directory (no slash appended)
        foldersAreAlbums (bool): if true, then the name of the \
            immediate folder containing each music file \
            is assumed to be the name of its associated album
        AAT_structure (bool): if True, the chosen folder is believed to follow \
            the Artist-Album-Track structure
        findArt (bool): if True, will attempt to find \
            album/track/artist art (in that order of priority) \
            on Spotify. Failing this, or if the argument is False \
            default Serenity art is selected.
    """
    if AAT_structure == True: foldersAreAlbums = False

    if directory == "": return
    i = 0
    for dir, subdirs, files in os.walk(directory):
        absdir = os.path.abspath(dir) # no appended slash
        fileDir = absdir + os.sep # full directory with an appended slash
        for fileName in files: 
            songData = __fileProcessing(
                fileDir, fileName, foldersAreAlbums, AAT_structure,
                findArt
            ) # may invert var foldersAreAlbums - see doc
            if songData == None:
                continue
            db.addSong(songData)
        if i == 0:
            if db.directoryRegistered(fileDir) == False:
                db.addDirectory(fileDir, folder_is_album=foldersAreAlbums, AAT_structure_structure=AAT_structure)
            i = 1
        


                    
               


                
                
                
                
                
                

                

                  

                   
                    
                
