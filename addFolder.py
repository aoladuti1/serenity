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
            duration = str(math.floor(track.duration/1000))
            bitRateInfo = track.other_bit_rate[0]
            samplingRateInfo = track.other_sampling_rate[0]
            channelCount = str(track.channel_s)
            audioFormat = track.other_format[0]
            return [duration, bitRateInfo, samplingRateInfo, channelCount, audioFormat] #returning here is an optimization
    return ["0", "0", "0", "0", "0"]

# Returns false if it fails to find or assign art
# music is either the track name or album name, dependent on if isAlbum is true
def dlArt(music, artist, artName, isAlbum):
    target = ART_PATH + artName + ".jpg"
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
                target = ART_PATH + artist + ".jpg"
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

def getSong(song, filePath, folderIsAlbum, AAT = True):
    """
    Get the artist and track from a song. A song may be within an AAT structure.
    An AAT (Artist-Album-Track) folder structure means inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files like so (with no exceptions):
    C:/Bryson Tiller/The Best Album Ever/The Best Track Ever.mp3

    Parameters:

    ~song: "bryson tiller - dont" for instance

    ~filePath: full path to the folder containing the file

    ~folderIsAlbum: if the folder addition is in album mode or not (for corner cases)

    Returns:
    
    array of {artist, album, track, trackNum}
    """
    structure = Path(filePath).parents
    folderName = filePath.split(os.sep)[-2] #filePath has an appended slash so we do -2 instead of -1
    if AAT == False or len(structure) < 2:
        return __getSongNoStructure(song, folderName, folderIsAlbum)
    else:
        artist = str(structure[0]).rpartition(os.sep)[-1]
        album = folderName
        d = ""
        info = getTrackInfo(song)
        track = info[1]
        trackNum = info[2]
        return [artist, album, track, trackNum]

def getParentAndFolderNames(filePath):
    try:
        folderName = filePath.split(os.sep)[-2]
        parentFolderName = filePath.split(os.sep)[-3]
    except:
        parentFolderName = '' #corner case - defensive programming isn't obsessive... right?
    if parentFolderName.endswith(':') == True:
        parentFolderName = parentFolderName[0:-1]
    else:
        if folderName.endswith(":") == True:
            folderName = folderName[0:-1] #for music a little below the a drive
            parentFolderName = ''
    return [parentFolderName, folderName]

def updateDB(filePath, songData):
    if db.directoryRegistered(filePath) == False:
        db.addDirectory(filePath)
    db.addSong(songData)

# Used by addFiles() and addFolders() -- see their docs
# note that filePath must have a slash (os.sep) appended
# Returns:
#     dict: a dictionary containing all song data, where the keys
#         correspond to a Song table column in the database, or None 
#         if the file is already present in the database
def __fileProcessing(
        filePath: str, fileName: str,
        foldersAreAlbums: bool, AAT: bool,
        findArt: bool, 
    ) -> dict:
    if AAT == True: foldersAreAlbums = False
    if fileName.endswith(SUPPORTED_EXTENSIONS):
        FQFN = filePath + fileName
        if db.songRegistered(FQFN) == True:
            return None
        song = fileName.rpartition(".")[0]
        folderName = filePath.split(os.sep)[-2]
        art = DEFAULT_ART
        (
            duration, bitRateInfo, samplingRateInfo, 
            channelCount, audioFormat 
        ) = getAudioInfo(FQFN)
        (
            artist, album, track, trackNum
        ) = getSong(song, filePath, foldersAreAlbums, AAT)
        hasAlbum = album != UNKNOWN_ALBUM
        (
            parentFolderName, folderName #may not correspond to harddrive
        ) = getParentAndFolderNames(filePath)
        if findArt == True:
            if hasAlbum == True:
                musicChoice = album
                artName = parentFolderName + "-" + folderName
            else:
                musicChoice = track
                artName = parentFolderName + "-" + folderName + "-" + song
            art = dlArt(musicChoice, artist, artName, hasAlbum)
        songData = {
            "FQFN": FQFN,
            "artist": artist, 
            "album": album,
            "track": track,
            "trackNum": trackNum, 
            "duration": duration,
            "bitRateInfo": bitRateInfo,
            "samplingRateInfo": samplingRateInfo, 
            "channelCount":channelCount, 
            "audioFormat": audioFormat, 
            "art": art, 
            "listens": 0,
            "startingSpeed": 1        
        }
        return songData


def addFiles(FQFNs: list[str], foldersAreAlbums = False, AAT = False,
            findArt = True):
    """Adds audio files and their data to the database.
    Argument FQFNs is intended to be an alias of
    the return value of tkinter.filedialog.askopenfilenames().
    AAT stands for Artist-Album-Track folder structure.
    An AAT folder structure means that inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files (with no exceptions).
    If you chose "The Best Song ever.mp3" as a file
    and set AAT = True, it may have the following fully-qualified filename:
    C:\Music\Bryson Tiller\The Best Album Ever\The Best Song Ever.mp3

        Note: if AAT == True then foldersAreAlbums will be set to False.
        AAT takes precedence.

    Audio files themselves should have the following filename format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if NEITHER argument
    AAT == True nor foldersAreAlbums == True:
        <artist> - <album>
    
    
    Args: 
        FQFNs (list[str]): all fully qualified filenames to add
        foldersAreAlbums (bool): if true, then the name of the \
            immediate folder each music file is contained within \
            is assumed to be its album/body of music
        AAT (bool): if True, the chosen folder is believed to follow \
            the Artist-Album-Track structure
        findArt (bool): if True, will attempt to find \
            album/track/artist art (in that order of priority) \
            on Spotify. Failing this, or if the argument is False \
            default Serenity art is selected.
        includeSubfolders (bool): if True, subfolders of the chosen \
            directory are scanned with the same arguments
        
    """
    for fqfn in FQFNs:
        FQFN = os.path.abspath(fqfn)
        pathAndName = FQFN.rpartition(os.sep)
        filePath=pathAndName[0] + os.sep
        fileName=pathAndName[2]
        songData = __fileProcessing(
            filePath=filePath,
            fileName=fileName,
            foldersAreAlbums=foldersAreAlbums,
            AAT=AAT,
            findArt=findArt
        ) #may invert var foldersAreAlbums!
        if songData==None: return
        updateDB(filePath, songData)        
    
def addFolder(directory: str, foldersAreAlbums = False, AAT = False, 
              findArt=True, includeSubfolders=True):
    """Adds audio files and their directories to the database.
    AAT stands for Artist-Album-Track folder structure.
    An AAT folder structure means that inside each Artist
    folder are all their Album folders, which themselves 
    contain audio files (with no exceptions). 
    The chosen folder is also believed to be at the highest level -
    that is to say it only directly contains folders with artist names.
    If you chose C:\Music as a folder and set AAT = True, one well-placed 
    song below it may have the fully qualified filename:
    C:\Music\Bryson Tiller\The Best Album Ever\The Best Song Ever.mp3

        Note: if AAT == True then foldersAreAlbums will be set to False.
        AAT takes precedence.

    Audio files themselves should have the following naming format:
        [track number] artist name - <track name>\n OR
        [track number] - <track name>\n OR
        <track name>\n
    Where <> = required and [] = optional\n
        (note these assume that '-' is the designated config.SPLITTERCHAR")

    Album folders must have the following naming format if neither arguments
    AAT == True nor foldersAreAlbums == True:
        <artist> - <album>
    
    
    Args: 
        directory (str): the chosen starting directory (no slash appended)
        foldersAreAlbums (bool): if true, then the name of the \
            immediate folder each music file is contained within \
            is assumed to be its album/body of music
        AAT (bool): if True, the chosen folder is believed to follow \
            the Artist-Album-Track structure
        findArt (bool): if True, will attempt to find \
            album/track/artist art (in that order of priority) \
            on Spotify. Failing this, or if the argument is False \
            default Serenity art is selected.
        includeSubfolders (bool): if True, subfolders of the chosen \
            directory are scanned with the same arguments
        
    Returns:
        dict: a dictionary containing all song data, where the keys \
            correspond to a Song table column in the database, or None \
            if the file is already present in the database
    """
    if directory == "": return
    if AAT == True: foldersAreAlbums = False
    for dir, subdirs, files in os.walk(directory):
        absdir = os.path.abspath(dir) #no appended slash
        filePath = absdir + os.sep #full directory with an appended slash
        for fileName in files: 
            songData = __fileProcessing(
                filePath, fileName, foldersAreAlbums, AAT,
                findArt
            )
            if songData == None: continue
            updateDB(filePath, songData)
        if includeSubfolders == False: break
        


                    
               


                
                
                
                
                
                

                

                  

                   
                    
                
